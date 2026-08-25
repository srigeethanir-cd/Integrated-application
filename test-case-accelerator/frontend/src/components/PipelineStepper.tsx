import { Check, Clock3, LockKeyhole } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAppState } from '../state/app-state'

const stages = [
  ['Project', '/projects'], ['Security Analysis', '/security-report'], ['Repository Analysis', '/pipeline/dependencies'], ['Test Targets', '/pipeline/understanding'],
  ['Unit Tests', '/pipeline/generation'], ['AI Verification', '/pipeline/verification'], ['Quality', '/pipeline/quality'], ['Runtime Validation', '/runtime-validation'],
] as const

export function PipelineStepper() {
  const { pathname } = useLocation(); const navigate = useNavigate(); const { activeProjectId, artifacts } = useAppState()
  const completed = [true, artifacts.securityScan?.status === 'completed', !!artifacts.dependency, !!artifacts.understanding, !!artifacts.generation, !!artifacts.verification, !!artifacts.quality, false]
  return <div className="stepper" aria-label="Pipeline progress">{stages.map(([label, path], index) => {
    const target = index === 1 || index === 7 ? `${path}/${activeProjectId}` : path
    const current = index === 1 ? pathname.startsWith('/security-report/') : index === 7 ? pathname.startsWith('/runtime-validation/') : pathname === path; const done = completed[index]; const prerequisiteDone = index === 2 ? completed[0] : index === 3 ? completed[1] && completed[2] : index > 0 && completed[index - 1]; const disabled = !activeProjectId || (!current && !done && !prerequisiteDone)
    return <button key={label} disabled={disabled} onClick={() => target && navigate(target)} className={`step ${done ? 'complete' : current ? 'current' : 'pending'} ${disabled ? 'soon' : ''}`}>
      <span>{done ? <Check size={15} /> : disabled ? <LockKeyhole size={15} /> : <Clock3 size={15} />}</span><div><strong>{label}</strong><small>{disabled ? 'Locked' : done ? 'Completed' : current ? 'Current' : 'Available'}</small></div>
    </button>
  })}</div>
}
