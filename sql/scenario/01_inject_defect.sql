-- DELIBERATE DEFECT (demo only).
-- Story: a product-master reload re-seasoned one SKU and inserted a second row instead of
-- updating the first. DIM_PRODUCT now has two rows for ST120-BLK-M, so every sales row for
-- that SKU joins twice in VW_WHOLESALE_SALES and the dashboard overstates net sales.
INSERT INTO DIM_PRODUCT
SELECT SKU, STYLE_ID, STYLE_NAME, COLOR, SIZE, CATEGORY, 'FW26', UNIT_COST, WHOLESALE_PRICE
FROM DIM_PRODUCT WHERE SKU = 'ST120-BLK-M';
