-- -- Table : Customer_Base Segmentation : Subscribers ,which doesnt refil in range of (0,91) days 

-- -- Variables:
-- - ID 
-- - last_payement_date
-- - last_charge_date




SELECT SUBS_ID as ID, 
         MAX(TXN_DATE) AS last_payment_date,
         SYSDATE - MAX(TXN_DATE) AS last_charge_date
  FROM DWH_COE_DATA.TRAN_PAYMENTS
  WHERE TXN_DATE >= SYSDATE - INTERVAL '3' MONTH
    AND CATEGORY IN ('Private Person', 'Family')
    AND BUSINESS = 'Mobile'
    AND ACCT_CATEG = 'Pre-paid'
  GROUP BY SUBS_ID