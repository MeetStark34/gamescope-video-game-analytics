export function WhyThisMatters({ children }: { children: string }) {
  return <aside className="why-this-matters"><span aria-hidden="true">Why this matters</span><p>{children}</p></aside>;
}
