export default function StatCard({ title, value, description, icon: Icon }) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <div>
          <p className="stat-title">{title}</p>
          <h2 className="stat-value">{value}</h2>
        </div>

        {Icon ? (
          <div className="stat-icon">
            <Icon size={22} />
          </div>
        ) : null}
      </div>

      {description ? <p className="stat-description">{description}</p> : null}
    </div>
  );
}