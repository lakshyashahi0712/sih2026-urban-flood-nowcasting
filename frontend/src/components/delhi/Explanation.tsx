// Rule-based contextual explanation of model states.
//
// This is NOT an AI/LLM feature: every sentence is assembled from the
// actual model outputs, provenance labels, and documented evidence
// attached to the data being explained. The label below is shown with
// every explanation so users can distinguish:
//   MODEL RESULT / OBSERVED DATA / DERIVED ANALYSIS / THIS EXPLANATION.

export interface ReachExplanationInput {
  reachId: string;
  hydraulicStatus: string;
  incomingFlowM3S: number | null;
  storageM3: number | null;
  transferredM3S: number | null;
  capacityM3S: number | null;
  balanceResidualM3S: number | null;
  classification: string;
  forcingProvenance?: string | null; // provenance of the step's forcing
}

export function explainReachState(inp: ReachExplanationInput): string[] {
  const lines: string[] = [];

  if (
    inp.hydraulicStatus.startsWith('BLOCKED') &&
    (inp.incomingFlowM3S === null || inp.incomingFlowM3S === undefined)
  ) {
    lines.push(
      `No computed inflow reaches ${inp.reachId} at this step: the forcing for this interval is UNKNOWN (documented absence in the evidence), so continuity is blocked rather than zero-filled.`,
    );
  } else if (inp.incomingFlowM3S !== null) {
    lines.push(
      `${inp.reachId} receives a model-derived inflow of ${inp.incomingFlowM3S.toFixed(1)} m³/s at this step (runoff transformation of the documented forcing).`,
    );
  }

  if (inp.storageM3 === null) {
    lines.push(
      `Storage is UNKNOWN: continuity could not close for this step, so no storage value is carried forward (missing data is never replaced by zero).`,
    );
  } else {
    lines.push(
      `Continuity closed: storage is ${inp.storageM3.toLocaleString()} m³ with mass-balance residual ${inp.balanceResidualM3S !== null ? inp.balanceResidualM3S.toExponential(1) : '—'} m³/s.`,
    );
  }

  if (inp.classification === 'UNKNOWN') {
    lines.push(
      `The hydraulic state (dry / within capacity / surcharged) is UNKNOWN: classifying it requires a stage, and no storage–stage relation exists for Kushak — the model refuses to invent one.`,
    );
  }

  lines.push(
    `Outflow is transferred downstream only through the explicit transfer contract; ${inp.reachId === 'OC-02' ? 'OC-02 is the terminal reach and no outfall boundary (e.g. the Yamuna) is assumed.' : 'capacity is never silently substituted for actual outflow.'}`,
  );

  return lines;
}

export const EXPLANATION_LABEL =
  'Automated explanation — assembled from model outputs and evidence labels (rule-based, not AI-generated).';

const Explanation = ({
  lines,
  onClose,
}: {
  lines: string[];
  onClose: () => void;
}) => (
  <div className="explanation-box" role="note">
    <div className="explanation-head">
      <span className="explanation-title">WHY THIS STATE</span>
      <button className="explanation-close" onClick={onClose} aria-label="Close explanation">
        ×
      </button>
    </div>
    <ul className="explanation-lines">
      {lines.map((l, i) => (
        <li key={i}>{l}</li>
      ))}
    </ul>
    <div className="explanation-label">{EXPLANATION_LABEL}</div>
  </div>
);

export default Explanation;
