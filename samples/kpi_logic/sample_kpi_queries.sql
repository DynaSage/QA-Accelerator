-- KPI: Active Users Count
SELECT COUNT(DISTINCT user_id) AS active_users
FROM main.analytics.fact_sessions
WHERE session_date = CURRENT_DATE()

-- KPI: Revenue Mismatch
SELECT o.order_id, o.amount AS ui_amount, s.amount AS source_amount
FROM main.app.orders o
LEFT JOIN main.raw.orders s ON o.order_id = s.order_id
WHERE o.amount <> s.amount
