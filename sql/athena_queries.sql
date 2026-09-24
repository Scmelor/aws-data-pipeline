-- Consultas de ejemplo en Amazon Athena sobre las tablas creadas por el Glue Crawler.
-- Base de datos: transactions_db  |  Tablas: transactions (clean), daily_kpis (curated)

-- 1. Volumen aprobado y ticket promedio por canal
SELECT channel,
       SUM(n_transactions)                AS transactions,
       ROUND(SUM(approved_volume_cop), 0) AS approved_volume_cop,
       ROUND(AVG(avg_ticket_cop), 0)      AS avg_ticket_cop
FROM transactions_db.daily_kpis
GROUP BY channel
ORDER BY approved_volume_cop DESC;

-- 2. Tasa de rechazo mensual por canal
SELECT date_trunc('month', event_date) AS month,
       channel,
       ROUND(AVG(rejection_rate) * 100, 2) AS rejection_rate_pct
FROM transactions_db.daily_kpis
GROUP BY 1, 2
ORDER BY 1, 2;

-- 3. Top 10 ciudades por usuarios activos (aprovecha partition pruning por event_date)
SELECT city, COUNT(DISTINCT user_id) AS active_users
FROM transactions_db.transactions
WHERE event_date BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'
GROUP BY city
ORDER BY active_users DESC
LIMIT 10;
