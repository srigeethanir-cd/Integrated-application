"""
Analysis & Pipeline Cache Service – Redis Memory & SHA-256 Content Hashing.

Manages caching for:
1. File-level AST analysis caching (AnalysisCacheManager)
2. Project & Pipeline execution caching in Redis (RedisPipelineCacheManager)
3. Instant retrieval of previously executed ZIP/folder runs via SHA-256 content hashes
4. Redis in-memory storage for standard demo mock projects (React E-Commerce, Angular Customer, Vue Task Manager)
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


def get_redis_client():
    """Create a Redis client instance from environment variables."""
    if redis is None:
        return None
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        client = redis.from_url(redis_url, decode_responses=True, socket_timeout=3, socket_connect_timeout=3)
        client.ping()
        return client
    except Exception as exc:
        logger.debug("Redis connection to %s unavailable, falling back to in-memory/disk cache: %s", redis_url, exc)
        return None


def compute_project_content_hash(target: Union[str, bytes, Path]) -> str:
    """Compute deterministic SHA-256 hash of project source files or raw zip bytes."""
    hasher = hashlib.sha256()

    if isinstance(target, bytes):
        hasher.update(target)
        return hasher.hexdigest()

    target_path = Path(target)
    if not target_path.exists():
        return hashlib.sha256(str(target).encode("utf-8")).hexdigest()

    if target_path.is_file():
        try:
            with open(target_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return hashlib.sha256(str(target).encode("utf-8")).hexdigest()

    # If directory, hash all relevant source files in deterministic sorted order
    relevant_extensions = {".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".vue"}
    ignored_dirs = {
        "node_modules", ".git", "dist", "build", "coverage", "__pycache__", ".next",
        "runs", "generated_tests", "reports", "tests", "temp", "uploads", "project-1", ".turbo"
    }
    ignored_files = {"package-lock.json", "project_meta.json", "jest.config.json"}

    file_entries: List[Tuple[str, Path]] = []
    try:
        # Check package.json if exists
        pkg_json = target_path / "package.json"
        if pkg_json.is_file():
            file_entries.append(("package.json", pkg_json))

        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".") and "report" not in d.lower() and "run" not in d.lower()]
            for file in files:
                if file in ignored_files or file.startswith("jest-results-") or file.startswith("coverage-"):
                    continue
                # Ignore generated test files from hash calculation so re-runs remain stable
                if ".test." in file or ".spec." in file:
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in relevant_extensions:
                    full_p = Path(root) / file
                    rel_p = str(full_p.relative_to(target_path)).replace("\\", "/")
                    file_entries.append((rel_p, full_p))

        file_entries.sort(key=lambda x: x[0])
        for rel_p, full_p in file_entries:
            hasher.update(rel_p.encode("utf-8"))
            try:
                with open(full_p, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
            except Exception:
                pass
    except Exception as exc:
        logger.debug("Error computing directory content hash: %s", exc)

    return hasher.hexdigest()


class RedisPipelineCacheManager:
    """Manages project-level pipeline caching in Redis."""

    def __init__(self):
        self._redis = get_redis_client()
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._prefix = "unittest:pipeline:"
        self._project_prefix = "unittest:project_hash:"
        self._demo_prefix = "unittest:demo_project:"

    @property
    def is_redis_online(self) -> bool:
        """Check if Redis connection is active."""
        if not self._redis:
            self._redis = get_redis_client()
        return bool(self._redis)

    def get_cached_pipeline(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve completed pipeline execution results by project content hash."""
        if not content_hash:
            return None

        key = f"{self._prefix}{content_hash}"
        # 1. Try Redis
        if self.is_redis_online:
            try:
                raw = self._redis.get(key)
                if raw:
                    logger.info("⚡ Redis Cache HIT for project content hash: %s...", content_hash[:12])
                    data = json.loads(raw)
                    data["from_cache"] = True
                    data["cache_source"] = "redis"
                    return data
            except Exception as exc:
                logger.warning("Redis get error for key %s: %s", key, exc)

        # 2. Fallback to memory
        if key in self._local_cache:
            logger.info("⚡ Memory Cache HIT for project content hash: %s...", content_hash[:12])
            data = self._local_cache[key]
            data["from_cache"] = True
            data["cache_source"] = "memory"
            return data

        return None

    def set_cached_pipeline(
        self,
        content_hash: str,
        pipeline_output: Dict[str, Any],
        project_name: str = "",
        framework: str = "",
        ttl_seconds: int = 86400 * 14,  # 14 days
    ) -> None:
        """Store completed pipeline execution results into Redis cache."""
        if not content_hash or not pipeline_output:
            return

        key = f"{self._prefix}{content_hash}"
        payload = {
            "content_hash": content_hash,
            "project_name": project_name,
            "framework": framework,
            "pipeline_output": pipeline_output,
            "cached_at": time_now_iso(),
        }

        # 1. Store in memory
        self._local_cache[key] = payload

        # 2. Store in Redis
        if self.is_redis_online:
            try:
                self._redis.setex(key, ttl_seconds, json.dumps(payload))
                logger.info("💾 Cached completed pipeline output to Redis (key: %s...)", content_hash[:12])
            except Exception as exc:
                logger.warning("Redis setex error for key %s: %s", key, exc)

    def link_project_to_hash(self, project_id: str, content_hash: str) -> None:
        """Map project_id to its content hash."""
        if not project_id or not content_hash:
            return
        key = f"{self._project_prefix}{project_id}"
        if self.is_redis_online:
            try:
                self._redis.setex(key, 86400 * 30, content_hash)
            except Exception:
                pass
        self._local_cache[key] = {"hash": content_hash}

    def get_hash_for_project(self, project_id: str) -> Optional[str]:
        """Get content hash for a project ID."""
        if not project_id:
            return None
        key = f"{self._project_prefix}{project_id}"
        if self.is_redis_online:
            try:
                val = self._redis.get(key)
                if val:
                    return val
            except Exception:
                pass
        entry = self._local_cache.get(key)
        return entry.get("hash") if entry else None

    def seed_mock_projects_to_redis(self) -> None:
        """Seed the 3 demo mock projects directly into Redis memory."""
        demo_projects = [
            {
                "id": "proj_mock_react_ecommerce",
                "project_name": "React E-Commerce Portal",
                "framework": "React 18",
                "status": "completed",
                "source_file_count": 24,
                "pipeline_runs_count": 1,
                "test_cases_count": 4,
                "test_files_count": 2,
                "latest_run": {
                    "id": "run_mock_react_001",
                    "status": "completed",
                    "current_stage": "validation",
                    "progress": 1.0,
                    "started_at": "2026-08-25T10:00:00Z",
                },
                "latest_report": {
                    "total_tests": 4,
                    "passed": 4,
                    "failed": 0,
                    "pass_rate": 100.0,
                    "overall_quality_score": 98.0,
                },
                "created_at": "2026-08-25T10:00:00Z",
                "test_cases": [
                    {
                        "id": "TC-REACT-001",
                        "component": "ShoppingCart",
                        "title": "Verify Shopping Cart rendering with items",
                        "objective": "Verify that shopping cart correctly lists all added products and updates badge count.",
                        "category": "State",
                        "priority": "High",
                        "steps": [
                            "1. Render ShoppingCart component with mock list containing 3 items",
                            "2. Assert that item list contains exactly 3 entries",
                            "3. Assert that badge count in header displays '3'"
                        ],
                        "expected_result": "Cart shows 3 items, layout displays correct item list, badge displays '3'."
                    },
                    {
                        "id": "TC-REACT-002",
                        "component": "ShoppingCart",
                        "title": "Verify quantity increment updates total price",
                        "objective": "Verify that clicking quantity increment triggers state updates and total calculation.",
                        "category": "Events",
                        "priority": "High",
                        "steps": [
                            "1. Render ShoppingCart with single item priced $10 and quantity 1",
                            "2. Click the increment (+) button for the item",
                            "3. Verify quantity updates to 2 and subtotal changes to $20"
                        ],
                        "expected_result": "Quantity incremented to 2 and subtotal changes dynamically to $20."
                    },
                    {
                        "id": "TC-REACT-003",
                        "component": "PaymentForm",
                        "title": "Verify payment submission form validation",
                        "objective": "Verify that submit blocks and raises error notifications when fields are incomplete.",
                        "category": "Forms",
                        "priority": "High",
                        "steps": [
                            "1. Render PaymentForm with empty card details",
                            "2. Click checkout button",
                            "3. Verify card number and expiry validation error displays are present"
                        ],
                        "expected_result": "Validation block prevents submission; errors highlighted on input fields."
                    },
                    {
                        "id": "TC-REACT-004",
                        "component": "PaymentForm",
                        "title": "Verify successful payment checkout callback",
                        "objective": "Verify payment gateway success invokes success callback and triggers route redirection.",
                        "category": "Services",
                        "priority": "High",
                        "steps": [
                            "1. Render PaymentForm and fill credit card details",
                            "2. Click Submit Payment",
                            "3. Verify payment API is called and success page routing is triggered"
                        ],
                        "expected_result": "Checkout proceeds successfully; routes user to invoice success page."
                    }
                ],
                "test_files": [
                    {
                        "component": "ShoppingCart",
                        "file_name": "ShoppingCart.test.jsx",
                        "content": "import React from 'react';\nimport { render, screen, fireEvent } from '@testing-library/react';\nimport ShoppingCart from './ShoppingCart';\n\ndescribe('ShoppingCart Component', () => {\n  it('renders with 3 items', () => {\n    const mockItems = [{ id: 1, name: 'Shoes', price: 50 }, { id: 2, name: 'Socks', price: 10 }];\n    render(<ShoppingCart items={mockItems} />);\n    expect(screen.getByText('Shoes')).toBeInTheDocument();\n  });\n});\n"
                    },
                    {
                        "component": "PaymentForm",
                        "file_name": "PaymentForm.test.jsx",
                        "content": "import React from 'react';\nimport { render, screen, fireEvent } from '@testing-library/react';\nimport PaymentForm from './PaymentForm';\n\ndescribe('PaymentForm Component', () => {\n  it('shows error messages on empty submission', () => {\n    render(<PaymentForm />);\n    fireEvent.click(screen.getByRole('button', { name: /checkout/i }));\n    expect(screen.getByText(/card number is required/i)).toBeInTheDocument();\n  });\n});\n"
                    }
                ]
            },
            {
                "id": "proj_mock_angular_customer",
                "project_name": "Angular Customer Portal",
                "framework": "Angular 16",
                "status": "completed",
                "source_file_count": 18,
                "pipeline_runs_count": 1,
                "test_cases_count": 3,
                "test_files_count": 2,
                "latest_run": {
                    "id": "run_mock_angular_001",
                    "status": "completed",
                    "current_stage": "validation",
                    "progress": 1.0,
                    "started_at": "2026-08-25T10:00:00Z",
                },
                "latest_report": {
                    "total_tests": 3,
                    "passed": 3,
                    "failed": 0,
                    "pass_rate": 100.0,
                    "overall_quality_score": 98.0,
                },
                "created_at": "2026-08-25T10:00:00Z",
                "test_cases": [
                    {
                        "id": "TC-NG-001",
                        "component": "CustomerListComponent",
                        "title": "Verify customer table loads list items",
                        "objective": "Verify that customer data table populates correctly when service resolves.",
                        "category": "Services",
                        "priority": "High",
                        "steps": [
                            "1. Initialize CustomerListComponent fixture with MockCustomerService",
                            "2. Trigger ngOnInit lifecycle hook",
                            "3. Assert customer rows match mocked array count"
                        ],
                        "expected_result": "Table displays all customer rows with accurate names and email columns."
                    }
                ],
                "test_files": [
                    {
                        "component": "CustomerListComponent",
                        "file_name": "customer-list.component.spec.ts",
                        "content": "import { ComponentFixture, TestBed } from '@angular/core/testing';\nimport { CustomerListComponent } from './customer-list.component';\n\ndescribe('CustomerListComponent', () => {\n  let component: CustomerListComponent;\n  let fixture: ComponentFixture<CustomerListComponent>;\n\n  beforeEach(async () => {\n    await TestBed.configureTestingModule({\n      declarations: [ CustomerListComponent ]\n    }).compileComponents();\n    fixture = TestBed.createComponent(CustomerListComponent);\n    component = fixture.componentInstance;\n    fixture.detectChanges();\n  });\n\n  it('should create', () => {\n    expect(component).toBeTruthy();\n  });\n});\n"
                    }
                ]
            },
            {
                "id": "proj_mock_vue_task",
                "project_name": "Vue Task Manager",
                "framework": "Vue 3",
                "status": "completed",
                "source_file_count": 12,
                "pipeline_runs_count": 1,
                "test_cases_count": 2,
                "test_files_count": 1,
                "latest_run": {
                    "id": "run_mock_vue_001",
                    "status": "completed",
                    "current_stage": "validation",
                    "progress": 1.0,
                    "started_at": "2026-08-25T10:00:00Z",
                },
                "latest_report": {
                    "total_tests": 2,
                    "passed": 2,
                    "failed": 0,
                    "pass_rate": 100.0,
                    "overall_quality_score": 96.0,
                },
                "created_at": "2026-08-25T10:00:00Z",
                "test_cases": [
                    {
                        "id": "TC-VUE-001",
                        "component": "TaskItem",
                        "title": "Verify toggle completed task item",
                        "objective": "Verify that clicking task checkbox emits completion event.",
                        "category": "Events",
                        "priority": "Medium",
                        "steps": [
                            "1. Mount TaskItem component with active task",
                            "2. Trigger change event on checkbox",
                            "3. Assert emitted 'update:status' payload"
                        ],
                        "expected_result": "Component emits updated task status to parent."
                    }
                ],
                "test_files": [
                    {
                        "component": "TaskItem",
                        "file_name": "TaskItem.spec.js",
                        "content": "import { mount } from '@vue/test-utils';\nimport TaskItem from './TaskItem.vue';\n\ndescribe('TaskItem.vue', () => {\n  it('renders task title', () => {\n    const wrapper = mount(TaskItem, { props: { title: 'Buy milk', done: false } });\n    expect(wrapper.text()).toContain('Buy milk');\n  });\n});\n"
                    }
                ]
            }
        ]

        if self.is_redis_online:
            try:
                self._redis.set("unittest:demo_projects_list", json.dumps([p["id"] for p in demo_projects]))
                for p in demo_projects:
                    self._redis.set(f"{self._demo_prefix}{p['id']}", json.dumps(p))
                logger.info("⚡ Seeded %d mock demo projects into Redis memory cache.", len(demo_projects))
            except Exception as exc:
                logger.warning("Failed seeding demo projects to Redis: %s", exc)

        for p in demo_projects:
            self._local_cache[f"{self._demo_prefix}{p['id']}"] = p

    def get_mock_projects_from_redis(self) -> List[Dict[str, Any]]:
        """Retrieve cached demo mock projects from Redis."""
        if self.is_redis_online:
            try:
                list_raw = self._redis.get("unittest:demo_projects_list")
                if list_raw:
                    ids = json.loads(list_raw)
                    projs = []
                    for pid in ids:
                        praw = self._redis.get(f"{self._demo_prefix}{pid}")
                        if praw:
                            projs.append(json.loads(praw))
                    if projs:
                        return projs
            except Exception as exc:
                logger.warning("Redis error fetching demo projects: %s", exc)

        return [v for k, v in self._local_cache.items() if k.startswith(self._demo_prefix)]

    def get_mock_project_details_from_redis(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve details of a cached demo mock project from Redis."""
        key = f"{self._demo_prefix}{project_id}"
        if self.is_redis_online:
            try:
                raw = self._redis.get(key)
                if raw:
                    return json.loads(raw)
            except Exception:
                pass
        return self._local_cache.get(key)


def time_now_iso() -> str:
    import datetime
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# Singleton instance
redis_pipeline_cache = RedisPipelineCacheManager()


class AnalysisCacheManager:
    """Manages file-level analysis caching with persistent disk storage."""

    def __init__(self, persistent_cache_dir: Optional[str] = None) -> None:
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
        self._persistent_cache_dir = persistent_cache_dir or "temp/analysis_cache"
        os.makedirs(self._persistent_cache_dir, exist_ok=True)

    @staticmethod
    def build_cache_key(file_path: str, file_hash: str, framework: str, project_id: Optional[str] = None) -> str:
        """Construct a unique SHA-256 cache key including project_id for cross-project isolation."""
        pid = project_id or "default_project"
        raw = f"{pid}:{file_path}:{file_hash}:{framework.lower()}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, file_path: str, file_hash: str, framework: str, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached component analysis if valid for this specific project_id."""
        if not file_hash:
            self._misses += 1
            return None

        cache_key = self.build_cache_key(file_path, file_hash, framework, project_id=project_id)

        # 1. Check in-memory cache
        if cache_key in self._memory_cache:
            self._hits += 1
            return self._memory_cache[cache_key]

        # 2. Check persistent disk cache
        disk_file = os.path.join(self._persistent_cache_dir, f"{cache_key}.json")
        if os.path.exists(disk_file):
            try:
                with open(disk_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                self._memory_cache[cache_key] = cached_data
                self._hits += 1
                return cached_data
            except Exception as exc:
                logger.warning("Failed reading disk cache for key %s: %s", cache_key, exc)

        self._misses += 1
        return None

    def set(self, file_path: str, file_hash: str, framework: str, data: Dict[str, Any], project_id: Optional[str] = None) -> None:
        """Store component analysis in memory and disk cache."""
        if not file_hash or not data:
            return

        cache_key = self.build_cache_key(file_path, file_hash, framework, project_id=project_id)
        self._memory_cache[cache_key] = data

        disk_file = os.path.join(self._persistent_cache_dir, f"{cache_key}.json")
        try:
            with open(disk_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            logger.warning("Failed writing disk cache for key %s: %s", cache_key, exc)

    def get_stats(self) -> Tuple[int, int, float]:
        """Return tuple of (hits, misses, hit_rate_percentage)."""
        total = self._hits + self._misses
        hit_rate = round((self._hits / total * 100.0), 2) if total > 0 else 0.0
        return self._hits, self._misses, hit_rate

    def reset_stats(self) -> None:
        """Reset hit/miss performance counters."""
        self._hits = 0
        self._misses = 0

    def save_run_cache(self, run_dir: str) -> None:
        """Persist current run's active cache entries to run directory."""
        try:
            run_cache_file = os.path.join(run_dir, "cache_summary.json")
            hits, misses, hit_rate = self.get_stats()
            summary = {
                "hits": hits,
                "misses": misses,
                "hit_rate_percent": hit_rate,
                "cached_entries": len(self._memory_cache)
            }
            with open(run_cache_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        except Exception as exc:
            logger.warning("Failed persisting run cache summary: %s", exc)
