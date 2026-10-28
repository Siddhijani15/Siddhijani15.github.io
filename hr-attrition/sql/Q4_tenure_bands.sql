-- Q4: Tenure bands for leavers
-- ================================
-- This query groups all leavers into tenure bands based on TenureAtExit:
--   - Under 1 year:   tenure less than 1 year
--   - 1-3 years:      tenure 1 to under 3 years
--   - 3-5 years:      tenure 3 to under 5 years
--   - 5+ years:       tenure 5 years or more
-- It shows the count and percentage for each band.
-- The first-year leavers (Under 1 year) are highlighted with a flag column.

-- CASE assigns each leaver to a tenure band based on their TenureAtExit value.
-- The second CASE sets 'YES' for the Under-1-year band so those rows stand out.
WITH tenure_bands AS (
    SELECT
        TenureAtExit,
        CASE
            WHEN TenureAtExit < 1  THEN 'Under 1 year'
            WHEN TenureAtExit < 3  THEN '1-3 years'
            WHEN TenureAtExit < 5  THEN '3-5 years'
            ELSE '5+ years'
        END AS tenure_band,
        CASE
            WHEN TenureAtExit < 1  THEN 'YES'
            ELSE 'NO'
        END AS first_year_flag
    FROM attrition_fact
    WHERE AttritionFlag = 'Yes'
      AND TenureAtExit IS NOT NULL
),

band_summary AS (
    SELECT
        tenure_band,
        COUNT(*) AS leaver_count,
        ROUND(
            100.0 * COUNT(*) / (SELECT COUNT(*) FROM tenure_bands), 2
        ) AS pct_of_leavers,
        -- Average tenure within this band for extra context
        ROUND(AVG(TenureAtExit), 2) AS avg_tenure
    FROM tenure_bands
    GROUP BY tenure_band
)

SELECT
    tenure_band,
    leaver_count,
    pct_of_leavers,
    avg_tenure,
    CASE WHEN tenure_band = 'Under 1 year' THEN '*** HIGH RISK ***' ELSE '' END AS highlight
FROM band_summary
ORDER BY
    CASE tenure_band
        WHEN 'Under 1 year' THEN 1
        WHEN '1-3 years'   THEN 2
        WHEN '3-5 years'   THEN 3
        WHEN '5+ years'    THEN 4
    END;
