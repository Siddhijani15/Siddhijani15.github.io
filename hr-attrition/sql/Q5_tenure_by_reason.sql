-- Q5: Tenure by exit reason
-- ================================
-- For each exit reason this query calculates:
--   - Average tenure (how long people stayed before leaving for this reason)
--   - Minimum tenure
--   - Maximum tenure
-- Only reasons with at least 5 exits are included (enforced with HAVING).
-- Results are sorted by shortest average tenure first, so reasons
-- that cause quick exits appear at the top.

SELECT
    ExitReason                                       AS exit_reason,
    COUNT(*)                                          AS exit_count,
    ROUND(AVG(TenureAtExit), 2)                      AS avg_tenure_years,
    ROUND(MIN(TenureAtExit), 2)                      AS min_tenure_years,
    ROUND(MAX(TenureAtExit), 2)                      AS max_tenure_years
FROM attrition_fact
WHERE AttritionFlag = 'Yes'
  AND ExitReason IS NOT NULL
  AND TenureAtExit IS NOT NULL

-- GROUP BY exit reason so each reason gets its own row
GROUP BY ExitReason

-- HAVING keeps only reasons with 5 or more exits (avoids unreliable averages)
HAVING COUNT(*) >= 5

-- Sort by shortest average tenure first
ORDER BY avg_tenure_years ASC;
