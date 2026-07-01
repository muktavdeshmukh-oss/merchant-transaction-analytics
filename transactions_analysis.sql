-- Importing transactions.csv
CREATE TABLE transactions (
    merchant_id TEXT,
    terminal_id TEXT,
    transaction_create_date TEXT,
    transaction_id TEXT,
    transaction_total_amount NUMERIC,
    merchant_registration_date TEXT,
    has_loyalty TEXT,
    transaction_currency TEXT,
    transaction_tip_amount NUMERIC,
    transaction_account_type TEXT,
    country TEXT
);

SELECT * FROM transactions LIMIT 10;
SELECT COUNT(*) FROM transactions;

-- Importing merchant_id_map.csv
CREATE TABLE merchant_id_map (
    old_merchant_id TEXT,
    new_merchant_id TEXT
);

SELECT * FROM merchant_id_map;
-------------------------------------------------------------
-- Joining both tables, mapping old merchant IDs to new merchant IDs, and adding transaction ranking


WITH mapped AS (
    SELECT 
        t.terminal_id,
        t.transaction_create_date,
        t.transaction_id,
        t.transaction_total_amount,
        t.merchant_registration_date,
        t.has_loyalty,
        t.transaction_currency,
        t.transaction_tip_amount,
        t.transaction_account_type,
        t.country,
        COALESCE(m.new_merchant_id, t.merchant_id) AS updated_merchant_id,
        CASE 
            WHEN m.old_merchant_id IS NOT NULL THEN 1
            ELSE 0
        END AS is_mapped
    FROM transactions t
    LEFT JOIN merchant_id_map m
        ON t.merchant_id = m.old_merchant_id
) --Part b. mapping CTE

SELECT *,
    ROW_NUMBER() OVER (
        PARTITION BY updated_merchant_id
        ORDER BY TO_TIMESTAMP(transaction_create_date, 'DD/MM/YYYY HH24:MI'),transaction_id) AS ranking
FROM mapped; -- Part c. adding ranking as the running count of transactions for each unique merchant ID sorted by transaction date

-- Sanity check: ensuring min ranking = 1 and max ranking = transaction count for each merchant
SELECT updated_merchant_id, MIN(ranking), MAX(ranking), COUNT(*)
FROM (
    WITH mapped AS (
        SELECT 
            t.terminal_id,
            t.transaction_create_date,
            t.transaction_id,
            t.transaction_total_amount,
            t.merchant_registration_date,
            t.has_loyalty,
            t.transaction_currency,
            t.transaction_tip_amount,
            t.transaction_account_type,
            t.country,
            COALESCE(m.new_merchant_id, t.merchant_id) AS updated_merchant_id,
            CASE 
                WHEN m.old_merchant_id IS NOT NULL THEN 1
                ELSE 0
            END AS is_mapped
        FROM transactions t
        LEFT JOIN merchant_id_map m
            ON t.merchant_id = m.old_merchant_id
    )
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY updated_merchant_id
            ORDER BY 
                TO_TIMESTAMP(transaction_create_date, 'DD/MM/YYYY HH24:MI'),
                transaction_id
        ) AS ranking
    FROM mapped
) x
GROUP BY updated_merchant_id
ORDER BY updated_merchant_id;

---------------------
-- Identifying the first merchant to transact in each onboarding cohort
WITH mapped AS (
    SELECT 
        t.terminal_id,
        t.transaction_create_date,
        t.transaction_id,
        t.transaction_total_amount,
        t.merchant_registration_date,
        t.has_loyalty,
        t.transaction_currency,
        t.transaction_tip_amount,
        t.transaction_account_type,
        t.country,
        COALESCE(m.new_merchant_id, t.merchant_id) AS updated_merchant_id,
        CASE 
            WHEN m.old_merchant_id IS NOT NULL THEN 1
            ELSE 0
        END AS is_mapped
    FROM transactions t
    LEFT JOIN merchant_id_map m
        ON t.merchant_id = m.old_merchant_id
),

merchant_first_txn AS (
    SELECT
        updated_merchant_id,
        TO_CHAR(
        DATE_TRUNC('month', TO_TIMESTAMP(merchant_registration_date, 'DD/MM/YYYY HH24:MI')),
    'Mon-YYYY') AS onboarding_month ,
        MIN(TO_TIMESTAMP(transaction_create_date, 'DD/MM/YYYY HH24:MI')) AS first_transaction_date
    FROM mapped
    GROUP BY 1,2
),

ranked AS (
    SELECT
        onboarding_month,
        updated_merchant_id,
        first_transaction_date,
        RANK() OVER (
            PARTITION BY onboarding_month
            ORDER BY first_transaction_date
        ) AS cohort_rank
    FROM merchant_first_txn
)
SELECT
    onboarding_month,
    updated_merchant_id,
    first_transaction_date
FROM ranked
WHERE cohort_rank = 1
ORDER BY onboarding_month;


