import { useEffect, useRef, useState, type DragEvent, type FormEvent, type KeyboardEvent } from 'react'
import { Check, CheckCircle2, ChevronDown, FileArchive, GitBranch, PackageOpen, Upload, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAppState, type WorkflowMode } from '../state/app-state'
import { Button, ErrorNotice } from './ui'

const projectNameFromFile = (file: File) => file.name.replace(/\.zip$/i, '').replace(/[-_]+/g, ' ').trim()
const readableSize = (bytes: number) => bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`

export function UploadModal() {
  const state = useAppState()
  const navigate = useNavigate()
  const fileInput = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [workflowMode, setWorkflowMode] = useState<WorkflowMode>('quick')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [projectName, setProjectName] = useState('')
  const [dragging, setDragging] = useState(false)
  const mode = state.uploadMode

  useEffect(() => {
    if (!mode) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    setSelectedFile(null)
    setProjectName('')
    setWorkflowMode('quick')
    setError('')
    return () => { document.body.style.overflow = previousOverflow }
  }, [mode])

  if (!mode) return null

  const selectFile = (file?: File) => {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.zip')) {
      setError('Select a ZIP archive ending in .zip')
      return
    }
    setSelectedFile(file)
    setProjectName(projectNameFromFile(file))
    setError('')
  }
  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    selectFile(event.dataTransfer.files[0])
  }
  const openPicker = () => fileInput.current?.click()
  const handleUploadKey = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return
    event.preventDefault()
    openPicker()
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (mode === 'zip' && !selectedFile) return
    setBusy(true)
    setError('')
    try {
      const data = new FormData(event.currentTarget)
      if (selectedFile) data.set('uploaded_file', selectedFile)
      const githubRequest = {
        name: String(data.get('name')),
        description: String(data.get('description') ?? ''),
        github_url: String(data.get('github_url')),
      }
      const project = mode === 'zip' ? await api.uploadProject(data) : await api.githubProject(githubRequest)
      const workflow = {
        project,
        current_stage: 'stage_1' as const,
        status: 'waiting_for_approval' as const,
        completed_stage: 'stage_1' as const,
        next_stage: 'stage_2' as const,
        security_scan: null,
        dependency: null,
        pipeline: null,
        generation: null,
        error: null,
        logs: ['Stage 1 project ingestion completed'],
      }
      state.setProjects([project, ...state.projects.filter((item) => item.id !== project.id)])
      state.closeUpload()
      state.beginApprovalWorkflow(workflow, workflowMode)
      navigate(`/processing/${project.id}`)
      if (workflowMode === 'quick') state.startQuickWorkflow(project)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Project could not be added')
    } finally {
      setBusy(false)
    }
  }

  const isZip = mode === 'zip'
  return <div className="modal-backdrop" role="presentation" onMouseDown={() => { if (!busy) state.closeUpload() }}>
    <div className={`modal project-import-modal ${isZip ? 'zip-generation-modal' : ''}`} role="dialog" aria-modal="true" aria-labelledby="upload-title" aria-describedby="upload-description" onMouseDown={(event) => event.stopPropagation()}>
      <div className="modal-head">
        <div className="modal-title-icon">{isZip ? <PackageOpen size={20} /> : <GitBranch size={20} />}</div>
        <div><h2 id="upload-title">{isZip ? 'Generate Unit Tests' : 'Import Project'}</h2><p id="upload-description">{isZip ? 'Upload a backend project and let TestForge analyze it, generate AI-powered unit tests, validate them, and prepare an exportable pytest suite.' : 'Import a public backend repository and generate its production-ready unit tests.'}</p></div>
        <button className="icon-button" aria-label="Close dialog" onClick={state.closeUpload} disabled={busy}><X size={18} /></button>
      </div>

      <form onSubmit={submit} className="form-stack">
        <div className="modal-content">
          {isZip ? <>
            <div className={`zip-dropzone ${dragging ? 'dragging' : ''} ${selectedFile ? 'selected' : ''}`} role="button" tabIndex={0} aria-label={selectedFile ? `Selected ZIP archive ${selectedFile.name}. Press Enter to replace it.` : 'Drop a ZIP archive here or press Enter to browse files'} onClick={openPicker} onKeyDown={handleUploadKey} onDragEnter={(event) => { event.preventDefault(); setDragging(true) }} onDragOver={(event) => event.preventDefault()} onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false) }} onDrop={handleDrop}>
              <input ref={fileInput} className="sr-only" name="uploaded_file_picker" type="file" accept=".zip,application/zip" tabIndex={-1} onChange={(event) => selectFile(event.target.files?.[0])} />
              {selectedFile ? <><span className="zip-selected-icon"><CheckCircle2 size={22} /></span><div><strong>{selectedFile.name}</strong><small>{readableSize(selectedFile.size)} · ZIP archive</small></div><Button type="button" variant="secondary" onClick={(event) => { event.stopPropagation(); openPicker() }}>Replace File</Button></> : <><span className="zip-upload-icon"><FileArchive size={26} /></span><div><strong>Drop your ZIP archive here</strong><small>or</small></div><Button type="button" variant="secondary" onClick={(event) => { event.stopPropagation(); openPicker() }}><Upload size={15} /> Browse Files</Button><p>Supported format <strong>ZIP (.zip)</strong></p></>}
            </div>

            <section className="project-information" aria-labelledby="project-information-title"><h3 id="project-information-title">Project Information</h3><div className="project-fields"><label>Project Name<input name="name" required value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="Project name" /></label><label>Description <small>Optional</small><textarea name="description" rows={2} placeholder="Repository context" /><em>Provide context if your repository requires special handling.</em></label></div></section>

            <details className="advanced-options"><summary><span>Advanced Options</span><ChevronDown size={16} /></summary><fieldset><legend>Workflow Mode</legend><label><input className="sr-only" type="radio" name="workflow_mode" value="quick" checked={workflowMode === 'quick'} onChange={() => setWorkflowMode('quick')} /><span className="workflow-option-copy"><span className="workflow-option-heading"><i className="workflow-option-check"><Check size={12} /></i><strong>Quick Mode</strong><em>Recommended</em></span><small>Automatically generates, verifies, and prepares the test suite.</small></span></label><label><input className="sr-only" type="radio" name="workflow_mode" value="review" checked={workflowMode === 'review'} onChange={() => setWorkflowMode('review')} /><span className="workflow-option-copy"><span className="workflow-option-heading"><i className="workflow-option-check"><Check size={12} /></i><strong>Review Mode</strong><em>Manual</em></span><small>Pause after each major step for user approval.</small></span></label></fieldset></details>
          </> : <>
            <label>Project name<input name="name" required placeholder="Customer API" /></label>
            <label>Public repository URL<input name="github_url" type="url" required placeholder="https://github.com/org/repository" /></label>
            <label>Description<textarea name="description" rows={3} placeholder="Optional project context" /></label>
          </>}
          {error && <ErrorNotice message={error} />}
        </div>
        <div className="modal-actions"><Button type="button" variant="secondary" onClick={state.closeUpload} disabled={busy}>Cancel</Button><Button loading={busy} disabled={isZip && !selectedFile}>{isZip ? 'Start Generation' : 'Import Project'}</Button></div>
      </form>
    </div>
  </div>
}
