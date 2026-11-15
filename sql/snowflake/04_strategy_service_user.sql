-- Snowflake-only. Read-only service login for Strategy (MicroStrategy).
-- It holds only WHS_REPORTING, so it can SELECT from the VW_* reporting views and nothing else.
-- The access token is generated separately (ALTER USER ... ADD PROGRAMMATIC ACCESS TOKEN)
-- and is never stored in Git.
USE ROLE ACCOUNTADMIN;
CREATE USER IF NOT EXISTS STRATEGY_REPORTING
  TYPE = SERVICE
  DEFAULT_ROLE = WHS_REPORTING
  DEFAULT_WAREHOUSE = WHS_DEMO_WH
  COMMENT = 'Read-only service login for the Strategy dashboard (demo)';
GRANT ROLE WHS_REPORTING TO USER STRATEGY_REPORTING;
-- Strategy Cloud has no fixed IP list for a trial, so allow the token without a network policy.
-- In production: attach a network policy with the BI platform's egress IPs instead.
CREATE AUTHENTICATION POLICY IF NOT EXISTS WHOLESALE_DEMO.DW.STRATEGY_PAT_POLICY
  PAT_POLICY = (NETWORK_POLICY_EVALUATION = ENFORCED_NOT_REQUIRED);
ALTER USER STRATEGY_REPORTING SET AUTHENTICATION POLICY WHOLESALE_DEMO.DW.STRATEGY_PAT_POLICY;
-- Undo: DROP USER STRATEGY_REPORTING;
