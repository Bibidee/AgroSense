export const ConsensusBadge = ({ label = "Consensus reached" }: { label?: string }) =>
  <span className="badge badge-consensus"><i className="dot dot-violet"></i>{label}</span>;

export const SourceOfTruthBadge = () =>
  <span className="badge badge-consensus">Source of truth · GenLayer</span>;

export const RiskBadge = ({ level }: { level: string }) =>
  <span className="badge badge-risk"><i className="dot dot-risk"></i>{level}</span>;

export const ActionWindowBadge = ({ window: w }: { window: string }) =>
  <span className="badge badge-gold"><i className="dot dot-gold"></i>{w}</span>;

export const LiveBadge = ({ label = "Live" }: { label?: string }) =>
  <span className="badge badge-sensor"><i className="dot dot-sensor pulse-consensus"></i>{label}</span>;

export const HealthBadge = ({ label = "Healthy" }: { label?: string }) =>
  <span className="badge badge-bio"><i className="dot dot-bio"></i>{label}</span>;
