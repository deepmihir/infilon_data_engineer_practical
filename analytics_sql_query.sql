-- Daily Active Users (DAU): count of distinct user_id per day.
SELECT 
    DATE(event_timestamp) AS event_date,
    COUNT(DISTINCT user_id) AS daily_active_users
FROM events
GROUP BY DATE(event_timestamp)
ORDER BY event_date;


-- Daily Purchases: total number of purchases and total revenue per day.
SELECT 
    DATE(event_timestamp) AS event_date,
    COUNT(*) AS total_purchases,
    SUM(amount) AS total_revenue
FROM events
WHERE event_type = 'purchase'
GROUP BY DATE(event_timestamp)
ORDER BY event_date;