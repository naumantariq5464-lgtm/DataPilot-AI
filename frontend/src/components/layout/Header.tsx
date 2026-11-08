interface HeaderProps {
  title:    string
  subtitle?: string
  actions?:  React.ReactNode
}

export default function Header({ title, subtitle, actions }: HeaderProps) {
  return (
    <div className="flex items-start justify-between px-6 py-5 border-b border-border bg-white">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && (
          <p className="text-muted mt-0.5">{subtitle}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 mt-0.5">
          {actions}
        </div>
      )}
    </div>
  )
}
