WITH CTE AS (
    SELECT SUBS_ID,
           MAX(TXN_DATE) AS last_payment_date,
           SYSDATE - MAX(TXN_DATE) AS last_charge
    FROM DWH_COE_DATA.TRAN_PAYMENTS
    WHERE TXN_DATE >= SYSDATE - INTERVAL '3' MONTH
      AND CATEGORY IN ('Private Person', 'Family')
      AND BUSINESS = 'Mobile'
      AND ACCT_CATEG = 'Pre-paid'
    GROUP BY SUBS_ID
),

     TC AS (
         SELECT subscriber_id, SUM(charge_total) AS total_charge
         FROM DWH_COE_DATA.PRJ_BCG_2208_TABLE3
         GROUP BY subscriber_id
     ),

     JF AS (
         SELECT CTE.SUBS_ID, CTE.last_charge, TC.total_charge
         FROM CTE
                  LEFT JOIN TC ON CTE.SUBS_ID = TC.subscriber_id
     ),

     SLD AS (
         SELECT
             subscriber_id,
             subs_first_activation_date,
             year_of_birth,
             gender,
             device_type_latest,
             subs_total_lifetime_charge
         FROM DWH_COE_DATA.PRJ_BCG_2208_TABLE1
     ),

     JS AS (
         SELECT *
         FROM JF
                  LEFT JOIN SLD ON JF.SUBS_ID = SLD.subscriber_id
     ),

     SLDL AS (
         SELECT subs_id, loc_region_name, loc_district_name, loc_street, device_type, device_brand, device_model
         FROM DWH_COE_DATA.HIER_SUBS
     ),

     JT AS (
         SELECT *
         FROM JS
                  LEFT JOIN SLDL ON JS.SUBS_ID = SLDL.subs_id
     )

SELECT * FROM JT




