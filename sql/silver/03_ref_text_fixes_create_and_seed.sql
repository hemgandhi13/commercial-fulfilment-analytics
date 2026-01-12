CREATE TABLE IF NOT EXISTS workspace.silver.ref_text_fixes (
  field STRING,          -- 'country' or 'city'
  bad_value STRING,
  good_value STRING
);

-- Countries seed 
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
