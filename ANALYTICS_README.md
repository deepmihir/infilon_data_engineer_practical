# Analytics Queries (MongoDB)

Analytics queries on the **`events`** collection in MongoDB (`etl_db.events`), populated by the ETL pipeline. Below are the MongoDB aggregation equivalents of the SQL in `analytics_sql_query.sql`, plus expected output descriptions. Add screenshots of your query results in the places indicated.

---

## 1. Daily Active Users (DAU)

**Definition:** Count of distinct `user_id` per day.

### SQL (reference)

```sql
SELECT 
    DATE(event_timestamp) AS event_date,
    COUNT(DISTINCT user_id) AS daily_active_users
FROM events
GROUP BY DATE(event_timestamp)
ORDER BY event_date;
```

### MongoDB aggregation

Run in MongoDB Shell, Compass, or any driver against the `events` collection:

```javascript
[
  {
    $group: {
      _id: {
        event_date: {
          $dateToString: {
            format: "%Y-%m-%d",
            date: "$event_timestamp"
          }
        },
        user_id: "$user_id"
      }
    }
  },
  {
    $group: {
      _id: "$_id.event_date",
      daily_active_users: { $sum: 1 }
    }
  },
  {
    $sort: { _id: 1 }
  }
]
```

### Output

One document per day with `_id` (date) and `daily_active_users` (count of distinct users that day).

*Screenshot of DAU query result:*

![Daily Active Users query output](screenshots/dau-output.png)

---

## 2. Daily Purchases

**Definition:** Total number of purchases and total revenue per day (only `event_type: "purchase"`).

### SQL (reference)

```sql
SELECT 
    DATE(event_timestamp) AS event_date,
    COUNT(*) AS total_purchases,
    SUM(amount) AS total_revenue
FROM events
WHERE event_type = 'purchase'
GROUP BY DATE(event_timestamp)
ORDER BY event_date;
```

### MongoDB aggregation

```javascript
[
  {
    $match: { event_type: "purchase" }
  },
  {
    $group: {
      _id: {
        $dateToString: {
          format: "%Y-%m-%d",
          date: "$event_timestamp"
        }
      },
      total_purchases: { $sum: 1 },
      total_revenue: { $sum: "$amount" }
    }
  },
  {
    $sort: { _id: 1 }
  }
]
```

### Output

One document per day with `_id` (date), `total_purchases` (count), and `total_revenue` (sum of `amount`).

*Screenshot of Daily Purchases query result:*

![Daily Purchases query output](screenshots/daily-purchases-output.png)

---

## How to run

- **MongoDB Compass:** Open the `events` collection → **Aggregations** tab → paste the pipeline stages (without the outer `[]` if your UI expects stage-by-stage).
- **MongoDB Shell:** `db.events.aggregate([ ... ])` with the full pipeline array.
- **Python (PyMongo):** `collection.aggregate([ ... ])`.

Ensure the ETL DAG has run at least once so `etl_db.events` is populated.

---

## Adding your screenshots

1. Create the `screenshots/` folder if it doesn’t exist.
2. Save your MongoDB query result screenshots as:
   - **`screenshots/dau-output.png`** — Daily Active Users result
   - **`screenshots/daily-purchases-output.png`** — Daily Purchases result

The images will then show up in the sections above.
