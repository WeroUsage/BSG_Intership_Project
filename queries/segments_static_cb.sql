
    SELECT static_data.*,
       Customer_bace.*
FROM
(
--- Customer_bace
(SELECT last_refill.*,
       last_topup.LAST_TOPUP_DATE,
       last_topup.DAYS_PASSED_LAST_TOPUP,
       last_topup.AMOUNT,
       last_topup.TOPUP_OFFER_NAME
FROM
(SELECT *
FROM(
  SELECT SUBS_ID,
  MAX(TXN_DATE) AS last_refill_date,
  SYSDATE - MAX(TXN_DATE) AS days_passed_last_refill
  From DWH_COE_DATA.TRAN_PAYMENTS
  WHERE TXN_DATE >= SYSDATE - INTERVAL '3' MONTH
  AND TOPUP_OFFER_NAME is NULL
  AND CATEGORY in ('Private Person', 'Family')
  AND BUSINESS = 'Mobile'
  AND AMOUNT > 0
  GROUP BY SUBS_ID
)
where days_passed_last_refill >=60
AND days_passed_last_refill <= 90) last_refill
LEFT JOIN
(SELECT p.SUBS_ID,
        max_payments.LAST_TOPUP_DATE,
        SYSDATE - max_payments.LAST_TOPUP_DATE AS days_passed_last_topup,
        p.AMOUNT,
        p.TOPUP_OFFER_NAME       
FROM DWH_COE_DATA.TRAN_PAYMENTS p
JOIN(
    SELECT SUBS_ID,
    MAX(TXN_DATE) AS LAST_TOPUP_DATE
    FROM DWH_COE_DATA.TRAN_PAYMENTS
    WHERE TXN_DATE <= SYSDATE - INTERVAL '60' DAY
    AND TXN_DATE >= SYSDATE - INTERVAL '3' MONTH
    AND TOPUP_OFFER_NAME is NOT NULL
    AND CATEGORY in ('Private Person', 'Family')
    AND BUSINESS = 'Mobile'
    AND AMOUNT > 0
    GROUP BY SUBS_ID) max_payments
ON p.SUBS_ID = max_payments.SUBS_ID
AND p.TXN_DATE = max_payments.LAST_TOPUP_DATE
) last_topup
ON last_refill.SUBS_ID = last_topup.SUBS_ID
) Customer_bace
--- static_data
LEFT JOIN
(SELECT SUBS_ID,
       ACTIVATION_DATE,
       STATUS_NAME,
       STATUS_DATE,
       STATUS_DESC_NAME,
       LOC_DISTRICT_NAME,
       LOC_REGION_NAME,
       DEVICE_CAT,
       DEVICE_TYPE,
       DEVICE_MODEL,
       BIRTH_DAY,
       GENDER
FROM DWH_COE_DATA.HIER_SUBS
WHERE coalesce(IS_GOVERNMENT, 'N') = 'N'
AND src = 'S'
AND prod_name = 'Mobile Phone'
AND cust_category IN ('Private Person', 'Family')
AND status_name IN ('Active','Partial')
AND service_no NOT IN (SELECT msisdn
                       FROM DWH_COE_DATA.HIER_SUBS_NOSMS
                       WHERE msisdn IS NOT NULL)
) static_data
ON static_data.SUBS_ID = Customer_bace.SUBS_ID
)
 
