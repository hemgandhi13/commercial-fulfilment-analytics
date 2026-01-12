# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS workspace.silver;
# MAGIC

# COMMAND ----------

### 01_silver_v1_create
%sql
CREATE OR REPLACE TABLE workspace.silver.dataco_supplychain_clean AS
WITH src AS (
  SELECT *
  FROM workspace.bronze.dataco_supplychain_raw_audited
),
parsed AS (
  SELECT
    src.*,
    COALESCE(
      to_timestamp(order_date_dateorders,   'M/d/yyyy H:mm'),
      to_timestamp(order_date_dateorders,   'MM/dd/yyyy HH:mm')
    ) AS order_ts_parsed,
    COALESCE(
      to_timestamp(shipping_date_dateorders,'M/d/yyyy H:mm'),
      to_timestamp(shipping_date_dateorders,'MM/dd/yyyy HH:mm')
    ) AS ship_ts_parsed
  FROM src
)
SELECT
  CAST(order_item_id AS BIGINT) AS order_item_id,
  CAST(order_id      AS BIGINT) AS order_id,
  CAST(customer_id   AS BIGINT) AS customer_id,
  CAST(product_card_id AS BIGINT) AS product_card_id,
  CAST(category_id     AS BIGINT) AS category_id,
  CAST(department_id   AS BIGINT) AS department_id,

  order_date_dateorders    AS order_ts_raw,
  shipping_date_dateorders AS ship_ts_raw,

  order_ts_parsed AS order_ts,
  ship_ts_parsed  AS ship_ts,

  to_date(order_ts_parsed) AS order_date,
  to_date(ship_ts_parsed)  AS ship_date,

  CAST(sales                    AS DOUBLE) AS gross_sales,
  CAST(order_item_total         AS DOUBLE) AS net_sales,
  CAST(order_item_discount      AS DOUBLE) AS discount_amount,
  CAST(order_item_discount_rate AS DOUBLE) AS discount_rate,
  CAST(order_profit_per_order   AS DOUBLE) AS profit,

  CAST(order_item_quantity      AS INT)    AS quantity,
  CAST(order_item_product_price AS DOUBLE) AS unit_price,
  CAST(product_price            AS DOUBLE) AS catalog_price,

  CAST(days_for_shipping_real        AS INT) AS days_for_shipping_real,
  CAST(days_for_shipment_scheduled   AS INT) AS days_for_shipment_scheduled,
  CAST(late_delivery_risk            AS INT) AS late_delivery_risk,

  CAST(delivery_status AS STRING) AS delivery_status,
  CAST(shipping_mode   AS STRING) AS shipping_mode,
  CAST(order_status    AS STRING) AS order_status,

  CAST(market      AS STRING) AS market,
  CAST(order_region AS STRING) AS order_region,

  CAST(order_country AS STRING) AS order_country,
  CAST(order_state   AS STRING) AS order_state,
  CAST(order_city    AS STRING) AS order_city,
  CAST(order_zipcode AS STRING) AS order_zipcode,

  CAST(customer_segment AS STRING) AS customer_segment,
  CAST(customer_country AS STRING) AS customer_country,
  CAST(customer_state   AS STRING) AS customer_state,
  CAST(customer_city    AS STRING) AS customer_city,
  CAST(customer_zipcode AS STRING) AS customer_zipcode,

  CAST(latitude  AS DOUBLE) AS latitude,
  CAST(longitude AS DOUBLE) AS longitude,

  CAST(product_name        AS STRING) AS product_name,
  CAST(product_category_id AS BIGINT) AS product_category_id,
  CAST(product_description AS STRING) AS product_description,
  CAST(product_status      AS BIGINT) AS product_status,

  CASE WHEN days_for_shipping_real > days_for_shipment_scheduled THEN 1 ELSE 0 END AS is_late_by_days,

  _ingest_ts,
  _batch_id

FROM parsed;


# COMMAND ----------

### 01_silver_v1_validations
-- A) Row counts: Bronze audited vs Silver v1
SELECT
  (SELECT COUNT(*) FROM workspace.bronze.dataco_supplychain_raw_audited) AS bronze_audited_rows,
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean)       AS silver_v1_rows;

-- B) Timestamp parse nulls (should be near 0)
SELECT
  SUM(CASE WHEN order_ts IS NULL THEN 1 ELSE 0 END) AS order_ts_nulls,
  SUM(CASE WHEN ship_ts  IS NULL THEN 1 ELSE 0 END) AS ship_ts_nulls,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean;

-- C) Key nulls
SELECT
  SUM(CASE WHEN order_item_id   IS NULL THEN 1 ELSE 0 END) AS null_order_item_id,
  SUM(CASE WHEN order_id        IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN customer_id     IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN product_card_id IS NULL THEN 1 ELSE 0 END) AS null_product_card_id
FROM workspace.silver.dataco_supplychain_clean;

-- D) Grain uniqueness check
SELECT
  COUNT(*) AS rows,
  COUNT(DISTINCT order_item_id) AS distinct_order_item_id
FROM workspace.silver.dataco_supplychain_clean;

-- E) Commercial sanity checks
SELECT
  MIN(discount_rate) AS min_discount_rate,
  MAX(discount_rate) AS max_discount_rate,
  MIN(net_sales)     AS min_net_sales,
  MIN(gross_sales)   AS min_gross_sales,
  MIN(profit)        AS min_profit
FROM workspace.silver.dataco_supplychain_clean;


# COMMAND ----------

### 02_silver_v2_standardise_keys
CREATE OR REPLACE TABLE workspace.silver.dataco_supplychain_clean_v2 AS
WITH base AS (
  SELECT * FROM workspace.silver.dataco_supplychain_clean
),
canon AS (
  SELECT
    b.*,

    regexp_replace(trim(b.order_region),  '\\s+', ' ') AS order_region_std,
    regexp_replace(trim(b.market),        '\\s+', ' ') AS market_std,
    regexp_replace(trim(b.shipping_mode), '\\s+', ' ') AS shipping_mode_std,

    regexp_replace(trim(b.order_country), '\\s+', ' ') AS order_country_std,
    regexp_replace(trim(b.order_state),   '\\s+', ' ') AS order_state_std,
    regexp_replace(trim(b.order_city),    '\\s+', ' ') AS order_city_std,
    CAST(b.order_zipcode AS STRING)                    AS order_zipcode_std,

    regexp_replace(trim(b.customer_country), '\\s+', ' ') AS customer_country_std,
    regexp_replace(trim(b.customer_state),   '\\s+', ' ') AS customer_state_std,
    regexp_replace(trim(b.customer_city),    '\\s+', ' ') AS customer_city_std,
    CAST(b.customer_zipcode AS STRING)                    AS customer_zipcode_std

  FROM base b
),
norm AS (
  SELECT
    c.*,

    -- Country canonicalisation (USA variants)
    CASE
      WHEN c.order_country_std IN ('EE. UU.', 'EE.UU.', 'EE UU', 'ESTADOS UNIDOS', 'Estados Unidos', 'United States', 'USA')
        THEN 'USA'
      ELSE upper(regexp_replace(regexp_replace(c.order_country_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' '))
    END AS order_country_key,

    upper(regexp_replace(regexp_replace(c.order_state_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_state_key,
    upper(regexp_replace(regexp_replace(c.order_city_std,  '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_city_key,
    upper(regexp_replace(regexp_replace(coalesce(c.order_zipcode_std,''), '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_zipcode_key,

    CASE
      WHEN c.customer_country_std IN ('EE. UU.', 'EE.UU.', 'EE UU', 'ESTADOS UNIDOS', 'Estados Unidos', 'United States', 'USA')
        THEN 'USA'
      ELSE upper(regexp_replace(regexp_replace(c.customer_country_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' '))
    END AS customer_country_key,

    upper(regexp_replace(regexp_replace(c.customer_state_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_state_key,
    upper(regexp_replace(regexp_replace(c.customer_city_std,  '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_city_key,
    upper(regexp_replace(regexp_replace(coalesce(c.customer_zipcode_std,''), '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_zipcode_key,

    upper(regexp_replace(regexp_replace(c.market_std,        '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS market_key,
    upper(regexp_replace(regexp_replace(c.order_region_std,  '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_region_key,
    upper(regexp_replace(regexp_replace(c.shipping_mode_std, '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS shipping_mode_key

  FROM canon c
)
SELECT * FROM norm;


# COMMAND ----------

### 02_silver_v2_validations
-- A) v1 vs v2 row counts (should match)
SELECT
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean)    AS silver_v1_rows,
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean_v2) AS silver_v2_rows;

-- B) How many rows were actually corrected by standardisation (proof metric)
SELECT
  SUM(CASE WHEN order_region <> order_region_std THEN 1 ELSE 0 END) AS region_corrected_rows,
  SUM(CASE WHEN market      <> market_std      THEN 1 ELSE 0 END) AS market_corrected_rows,
  SUM(CASE WHEN shipping_mode <> shipping_mode_std THEN 1 ELSE 0 END) AS shipmode_corrected_rows,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean_v2;

-- C) Encoding corruption counts (this is what triggered v3)
SELECT
  SUM(CASE WHEN order_country_std LIKE '%�%' THEN 1 ELSE 0 END) AS bad_country_rows,
  SUM(CASE WHEN order_city_std    LIKE '%�%' THEN 1 ELSE 0 END) AS bad_city_rows,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean_v2;

-- D) Zipcode nulls (data property; document, don’t “fix”)
SELECT
  SUM(CASE WHEN order_zipcode_std IS NULL THEN 1 ELSE 0 END) AS null_order_zip,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean_v2;


# COMMAND ----------

### 03_ref_text_fixes_create_and_seed
CREATE TABLE IF NOT EXISTS workspace.silver.ref_text_fixes (
  field STRING,          -- 'country' or 'city'
  bad_value STRING,
  good_value STRING
);

-- Countries seed (covers your entire bad_country_rows set)
MERGE INTO workspace.silver.ref_text_fixes
USING (
  SELECT col1 AS field, col2 AS bad_value, col3 AS good_value
  FROM VALUES
    ('country','M�xico','Mexico'),
    ('country','Espa�a','Espana'),
    ('country','Rep�blica Dominicana','Republica Dominicana'),
    ('country','Turqu�a','Turquia'),
    ('country','Panam�','Panama'),
    ('country','Pa�ses Bajos','Paises Bajos'),
    ('country','Ir�n','Iran'),
    ('country','Rep�blica Democr�tica del Congo','Republica Democratica del Congo'),
    ('country','Arabia Saud�','Arabia Saudi'),
    ('country','Per�','Peru'),
    ('country','Jap�n','Japon'),
    ('country','Pakist�n','Pakistan'),
    ('country','B�lgica','Belgica'),
    ('country','Hait�','Haiti'),
    ('country','Banglad�s','Banglades'),
    ('country','Camer�n','Camerun'),
    ('country','Kazajist�n','Kazajistan'),
    ('country','Sud�n','Sudan'),
    ('country','Rep�blica Checa','Republica Checa'),
    ('country','Hungr�a','Hungria'),
    ('country','Afganist�n','Afganistan'),
    ('country','Uzbekist�n','Uzbekistan'),
    ('country','N�ger','Niger'),
    ('country','Kirguist�n','Kirguistan'),
    ('country','Ben�n','Benin'),
    ('country','Azerbaiy�n','Azerbaiyan'),
    ('country','Pap�a Nueva Guinea','Papua Nueva Guinea'),
    ('country','Turkmenist�n','Turkmenistan'),
    ('country','Gab�n','Gabon'),
    ('country','T�nez','Tunez'),
    ('country','Emiratos �rabes Unidos','Emiratos Arabes Unidos'),
    ('country','Taiw�n','Taiwan'),
    ('country','Etiop�a','Etiopia'),
    ('country','Rep�blica Centroafricana','Republica Centroafricana'),
    ('country','L�bano','Libano'),
    ('country','Rep�blica del Congo','Republica del Congo'),
    ('country','Om�n','Oman'),
    ('country','Tayikist�n','Tayikistan'),
    ('country','Sud�n del Sur','Sudan del Sur'),
    ('country','Rep�blica de Gambia','Republica de Gambia'),
    ('country','But�n','Butan'),
    ('country','Bar�in','Barein'),
    ('country','S�hara Occidental','Sahara Occidental')
) s
ON workspace.silver.ref_text_fixes.field = s.field
AND workspace.silver.ref_text_fixes.bad_value = s.bad_value
WHEN MATCHED THEN UPDATE SET good_value = s.good_value
WHEN NOT MATCHED THEN INSERT (field, bad_value, good_value)
VALUES (s.field, s.bad_value, s.good_value);


# COMMAND ----------

### 03_ref_text_fixes_upsert_city_batch
MERGE INTO workspace.silver.ref_text_fixes
USING (
  SELECT col1 AS field, col2 AS bad_value, col3 AS good_value
  FROM VALUES
    ('city','Berl�n','Berlín'),
    ('city','S�o Paulo','São Paulo'),
    ('city','Le�n','León'),
    ('city','Ju�rez','Juárez'),
    ('city','Bogot�','Bogotá'),
    ('city','Dubl�n','Dublín'),
    ('city','Rang�n','Rangún'),
    ('city','M�rida','Mérida'),
    ('city','Shangh�i','Shanghái'),
    ('city','Holgu�n','Holguín'),
    ('city','Se�l','Seúl'),
    ('city','Coyoac�n','Coyoacán'),
    ('city','Camag�ey','Camagüey'),
    ('city','San Pedro de Macor�s','San Pedro de Macorís'),
    ('city','Medell�n','Medellín'),
    ('city','Quer�taro','Querétaro'),
    ('city','Bras�lia','Brasília'),
    ('city','Culiac�n','Culiacán'),
    ('city','C�rdoba','Córdoba'),
    ('city','Guant�namo','Guantánamo'),
    ('city','G�mez Palacio','Gómez Palacio'),
    ('city','Pek�n','Pekín'),
    ('city','Pinar del R�o','Pinar del Río'),
    ('city','San Luis Potos�','San Luis Potosí'),
    ('city','Estel�','Estelí'),
    ('city','San Francisco de Macor�s','San Francisco de Macorís'),
    ('city','Torre�n','Torreón'),
    ('city','Tuxtla Guti�rrez','Tuxtla Gutiérrez'),
    ('city','Canc�n','Cancún'),
    ('city','Arraij�n','Arraiján'),
    ('city','Consolaci�n del Sur','Consolacion del Sur'),
    ('city','San Mart�n','San Martin'),
    ('city','Ciego de �vila','Ciego de Avila'),
    ('city','San Jos� de las Lajas','San Jose de las Lajas'),
    ('city','J�rkov','Jarkov'),
    ('city','S�o Miguel dos Campos','Sao Miguel dos Campos'),
    ('city','C�cuta','Cucuta'),
    ('city','Antiguo Cuscatl�n','Antiguo Cuscatlan'),
    ('city','Or�n','Oran'),
    ('city','Cheli�binsk','Cheliabinsk'),
    ('city','Montr�al','Montreal'),
    ('city','Amatitl�n','Amatitlan'),
    ('city','Sancti Sp�ritus','Sancti Spiritus'),
    ('city','Col�n','Colon'),
    ('city','Goi�nia','Goiania'),
    ('city','Ararangu�','Ararangua'),
    ('city','C�rdenas','Cardenas'),
    ('city','V�nnytsia','Vinnytsia'),
    ('city','A�u','Acu'),
    ('city','Jo�o Pessoa','Joao Pessoa'),
    ('city','Jerusal�n','Jerusalen'),
    ('city','Tehuac�n','Tehuacan'),
    ('city','Nicol�s Romero','Nicolas Romero'),
    ('city','Chisin�u','Chisinau'),
    ('city','Macap�','Macapa'),
    ('city','S�o Lu�s','Sao Luis'),
    ('city','Aragua�na','Araguaina'),
    ('city','Obreg�n','Obregon'),
    ('city','San Andr�s Tuxtla','San Andres Tuxtla'),
    ('city','Gona�ves','Goncalves'),
    ('city','Acu�a','Acuna'),
    ('city','Ibagu�','Ibague'),
    ('city','Ribeir�o Preto','Ribeirao Preto'),
    ('city','Zany�n','Zanyon'),
    ('city','San Crist�bal de Las Casas','San Cristobal de Las Casas'),
    ('city','Vit�ria','Vitoria'),
    ('city','Teher�n','Teheran'),
    ('city','San Francisco del Rinc�n','San Francisco del Rincon'),
    ('city','Ban�','Bani'),
    ('city','Astan�','Astana'),
    ('city','Hamad�n','Hamadan'),
    ('city','Itaja�','Itajai'),
    ('city','S�o Gon�alo','Sao Goncalo'),
    ('city','Chapec�','Chapeco'),
    ('city','Macei�','Maceio'),
    ('city','Taubat�','Taubate'),
    ('city','Heroica Zit�cuaro','Heroica Zitacuaro'),
    ('city','G�mel','Gomel'),
    ('city','Soledad D�ez Guti�rrez','Soledad Diez Gutierrez'),
    ('city','Tecom�n','Tecoman'),
    ('city','Presidencia Roque S�enz Pe�a','Presidencia Roque Saenz Pena'),
    ('city','Balne�rio Cambori�','Balneario Camboriu'),
    ('city','Oca�a','Ocana'),
    ('city','Quixad�','Quixada'),
    ('city','Jequi�','Jequie'),
    ('city','Namang�n','Namangan'),
    ('city','T�nez','Tunez'),
    ('city','Fay�n','Fayon'),
    ('city','Santo Andr�','Santo Andre'),
    ('city','S�o Bernardo do Campo','Sao Bernardo do Campo'),
    ('city','S�o Leopoldo','Sao Leopoldo'),
    ('city','Maring�','Maringa'),
    ('city','Vor�nezh','Voronezh'),
    ('city','Oriximin�','Oriximina'),
    ('city','Astrac�n','Astracan'),
    ('city','Jos� Bonif�cio','Jose Bonifacio'),
    ('city','Boa Esperan�a','Boa Esperanca'),
    ('city','Fresnillo de Gonz�lez Echeverr�a','Fresnillo de Gonzalez Echeverria'),
    ('city','Santana de Parna�ba','Santana de Parnaiba'),
    ('city','B�lgorod','Belgorod'),
    ('city','San Nicol�s de los Arroyos','San Nicolas de los Arroyos'),
    ('city','Mossor�','Mossoro'),
    ('city','Bis�u','Bissau'),
    ('city','Ita�na','Itauna'),
    ('city','San Luis R�o Colorado','San Luis Rio Colorado'),
    ('city','Cuiab�','Cuiaba'),
    ('city','Cama�ari','Camacari'),
    ('city','Ca�ador','Cacador'),
    ('city','Jiz�n','Jizan'),
    ('city','Kostan�i','Kostanai'),
    ('city','Zhyt�myr','Zhytomyr'),
    ('city','Vi�a del Mar','Vina del Mar'),
    ('city','Ibi�na','Ibiuna'),
    ('city','Tup�','Tupa'),
    ('city','San Juan del R�o','San Juan del Rio'),
    ('city','El Lim�n','El Limon'),
    ('city','Teres�polis','Teresopolis'),
    ('city','Bah�a Blanca','Bahia Blanca'),
    ('city','Tiangu�','Tiangua'),
    ('city','Petr�polis','Petropolis'),
    ('city','Valpara�so','Valparaiso'),
    ('city','Graja�','Grajau'),
    ('city','Mor�n','Moron'),
    ('city','Paranagu�','Paranagua'),
    ('city','Potos�','Potosi'),
    ('city','Guaratinguet�','Guaratingueta'),
    ('city','Matur�n','Maturin'),
    ('city','Ocotl�n','Ocotlan'),
    ('city','Lora del R�o','Lora del Rio'),
    ('city','Valpara�so de Goi�s','Valparaiso de Goias'),
    ('city','Gravata�','Gravatai'),
    ('city','Garza Garc�a','Garza Garcia'),
    ('city','Ja�','Jau'),
    ('city','Guzm�n','Guzman'),
    ('city','Tabo�o da Serra','Taboao da Serra'),
    ('city','S�o Benedito','Sao Benedito'),
    ('city','Cassil�ndia','Cassilandia'),
    ('city','Apatzing�n de la Constituci�n','Apatzingan de la Constitucion'),
    ('city','Vlad�mir','Vladimir'),
    ('city','Ara�atuba','Aracatuba'),
    ('city','S�o Pedro da Aldeia','Sao Pedro da Aldeia'),
    ('city','Chill�n','Chillon'),
    ('city','Jundia�','Jundiai'),
    ('city','Francisco Beltr�o','Francisco Beltrao'),
    ('city','Bol�var','Bolivar'),
    ('city','Jers�n','Jerson'),
    ('city','Neuqu�n','Neuquen'),
    ('city','Sahuayo de Jos� Mar�a Morelos','Sahuayo de Jose Maria Morelos'),
    ('city','Jamund�','Jamundi'),
    ('city','Karagand�','Karaganda'),
    ('city','Cuman�','Cumana'),
    ('city','Cuautitl�n','Cuautitlan'),
    ('city','Santar�m','Santarem'),
    ('city','Los �ngeles','Los Angeles'),
    ('city','Bragan�a Paulista','Braganca Paulista'),
    ('city','Paran�','Parana'),
    ('city','Jacare�','Jacarei'),
    ('city','K�tahya','Kutahya'),
    ('city','Bag�','Bage'),
    ('city','Crici�ma','Criciuma'),
    ('city','Mau�','Maua'),
    ('city','Sim�es Filho','Simoes Filho'),
    ('city','�st� nad Labem','Usti nad Labem'),
    ('city','C�a','Cua'),
    ('city','Sumar�','Sumare'),
    ('city','Asunci�n','Asuncion'),
    ('city','Ibirit�','Ibirite'),
    ('city','�guas Lindas de Goi�s','Aguas Lindas de Goias'),
    ('city','Niter�i','Niteroi'),
    ('city','Teziutl�n','Teziutlan'),
    ('city','Tern�pil','Ternopil'),
    ('city','Ac�mbaro','Acambaro'),
    ('city','Rub�','Rubi'),
    ('city','San Crist�bal','San Cristobal'),
    ('city','Bento Gon�alves','Bento Goncalves'),
    ('city','Bug�a','Buga'),
    ('city','S�o Jos� dos Campos','Sao Jose dos Campos'),
    ('city','Qazv�n','Qazvin'),
    ('city','Ji-Paran�','Ji-Parana'),
    ('city','Rol�ndia','Rolandia'),
    ('city','Po�os de Caldas','Pocos de Caldas'),
    ('city','Guaruj�','Guaruja'),
    ('city','Vit�ria da Conquista','Vitoria da Conquista'),
    ('city','Quibd�','Quibdo'),
    ('city','Copiap�','Copiapo'),
    ('city','An�polis','Anapolis'),
    ('city','Facatativ�','Facatativa'),
    ('city','Pa�o do Lumiar','Paco do Lumiar'),
    ('city','Divin�polis','Divinopolis'),
    ('city','Uberl�ndia','Uberlandia'),
    ('city','S�o Vicente','Sao Vicente'),
    ('city','Vit�ria de Santo Ant�o','Vitoria de Santo Antao'),
    ('city','Hradec Kr�lov�','Hradec Kralove'),
    ('city','Iju�','Ijui'),
    ('city','B�char','Bechar'),
    ('city','Barra do Pira�','Barra do Pirai'),
    ('city','Cox�s B?z?r','Coxs Bazar'),
    ('city','Catal�o','Catalao'),
    ('city','Le Pr�-Saint-Gervais','Le Pre-Saint-Gervais'),
    ('city','Concepci�n del Uruguay','Concepcion del Uruguay'),
    ('city','Gir�n','Giron'),
    ('city','Len��is Paulista','Lencois Paulista'),
    ('city','Tatu�','Tatui'),
    ('city','�anakkale','Canakkale'),
    ('city','C�rtama','Cartama'),
    ('city','R�o Bravo','Rio Bravo'),
    ('city','Ilh�us','Ilheus'),
    ('city','Bing�l','Bingol'),
    ('city','Camb�','Cambe'),
    ('city','Bud�nnovsk','Budonnovsk'),
    ('city','Gravat�','Gravata'),
    ('city','Serop�dica','Seropedica'),
    ('city','V�rzea Grande','Varzea Grande'),
    ('city','L�bano','Libano'),
    ('city','Paysand�','Paysandu'),
    ('city','Arauc�ria','Araucaria'),
    ('city','Lambar�','Lambare'),
    ('city','San Jos� de Guanipa','San Jose de Guanipa'),
    ('city','Guimar�es','Guimaraes'),
    ('city','Palho�a','Palhoca'),
    ('city','Apartad�','Apartado'),
    ('city','Patroc�nio','Patrocinio'),
    ('city','L�zaro C�rdenas','Lazaro Cardenas'),
    ('city','Jata�','Jatai'),
    ('city','Eun�polis','Eunapolis'),
    ('city','Cubat�o','Cubatao'),
    ('city','G�nzburg','Gunzburg'),
    ('city','Ci�naga','Cienaga'),
    ('city','El Aai�n','El Aaiun'),
    ('city','Guam�chil','Guamuchil'),
    ('city','Carapicu�ba','Carapicuiba'),
    ('city','Semn�n','Semnan'),
    ('city','Jun�n','Junin'),
    ('city','Monter�a','Monteria'),
    ('city','Rondon�polis','Rondonopolis'),
    ('city','M�con','Macon'),
    ('city','Upplands V�sby','Upplands Vasby'),
    ('city','S�te','Sete')
) s
ON workspace.silver.ref_text_fixes.field = s.field
AND workspace.silver.ref_text_fixes.bad_value = s.bad_value
WHEN MATCHED THEN UPDATE SET good_value = s.good_value
WHEN NOT MATCHED THEN INSERT (field, bad_value, good_value)
VALUES (s.field, s.bad_value, s.good_value);


# COMMAND ----------

### 04_silver_v3_apply_mappings
CREATE OR REPLACE TABLE workspace.silver.dataco_supplychain_clean_v3 AS
WITH s AS (
  SELECT * FROM workspace.silver.dataco_supplychain_clean_v2
),
fx_country AS (
  SELECT bad_value, good_value
  FROM workspace.silver.ref_text_fixes
  WHERE field = 'country'
),
fx_city AS (
  SELECT bad_value, good_value
  FROM workspace.silver.ref_text_fixes
  WHERE field = 'city'
)
SELECT
  s.*,

  -- Clean display fields (order)
  COALESCE(fc.good_value,  s.order_country_std) AS order_country_clean,
  COALESCE(fci.good_value, s.order_city_std)    AS order_city_clean,

  -- Clean display fields (customer)
  COALESCE(fcc.good_value,    s.customer_country_std) AS customer_country_clean,
  COALESCE(fccity.good_value, s.customer_city_std)    AS customer_city_clean,

  -- Keys derived from clean display fields (stable for dims + hashing later)
  upper(regexp_replace(regexp_replace(COALESCE(fc.good_value, s.order_country_std),   '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_country_clean_key,
  upper(regexp_replace(regexp_replace(COALESCE(fci.good_value, s.order_city_std),     '[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS order_city_clean_key,

  upper(regexp_replace(regexp_replace(COALESCE(fcc.good_value, s.customer_country_std),'[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_country_clean_key,
  upper(regexp_replace(regexp_replace(COALESCE(fccity.good_value, s.customer_city_std),'[^\\p{L}\\p{N} ]', ''), '\\s+', ' ')) AS customer_city_clean_key

FROM s
LEFT JOIN fx_country fc    ON s.order_country_std    = fc.bad_value
LEFT JOIN fx_city    fci   ON s.order_city_std       = fci.bad_value
LEFT JOIN fx_country fcc   ON s.customer_country_std = fcc.bad_value
LEFT JOIN fx_city    fccity ON s.customer_city_std   = fccity.bad_value;


# COMMAND ----------

### 04_silver_v3_validations
-- A) Row count must remain stable across v1/v2/v3
SELECT
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean)     AS v1_rows,
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean_v2)  AS v2_rows,
  (SELECT COUNT(*) FROM workspace.silver.dataco_supplychain_clean_v3)  AS v3_rows;

-- B) Encoding corruption after mapping (goal: zero or near-zero)
SELECT
  SUM(CASE WHEN order_country_clean LIKE '%�%' THEN 1 ELSE 0 END) AS bad_order_country_after,
  SUM(CASE WHEN order_city_clean    LIKE '%�%' THEN 1 ELSE 0 END) AS bad_order_city_after,
  SUM(CASE WHEN customer_country_clean LIKE '%�%' THEN 1 ELSE 0 END) AS bad_customer_country_after,
  SUM(CASE WHEN customer_city_clean    LIKE '%�%' THEN 1 ELSE 0 END) AS bad_customer_city_after,
  COUNT(*) AS total_rows
FROM workspace.silver.dataco_supplychain_clean_v3;

-- C) Grain uniqueness
SELECT COUNT(*) AS rows, COUNT(DISTINCT order_item_id) AS distinct_order_item_id
FROM workspace.silver.dataco_supplychain_clean_v3;

-- D) Key nulls
SELECT
  SUM(CASE WHEN order_item_id   IS NULL THEN 1 ELSE 0 END) AS null_order_item_id,
  SUM(CASE WHEN order_id        IS NULL THEN 1 ELSE 0 END) AS null_order_id,
  SUM(CASE WHEN customer_id     IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
  SUM(CASE WHEN product_card_id IS NULL THEN 1 ELSE 0 END) AS null_product_card_id
FROM workspace.silver.dataco_supplychain_clean_v3;


# COMMAND ----------

### 05_silver_current_view
CREATE OR REPLACE VIEW workspace.silver.dataco_supplychain_clean_current AS
SELECT * FROM workspace.silver.dataco_supplychain_clean_v3;
