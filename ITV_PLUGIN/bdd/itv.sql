--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 16.4

-- Started on 2025-04-11 09:39:49

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 8 (class 2615 OID 23667)
-- Name: itv; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA itv;


ALTER SCHEMA itv OWNER TO postgres;

--
-- TOC entry 759 (class 1255 OID 23668)
-- Name: get_all_bcht_positions(); Type: FUNCTION; Schema: itv; Owner: postgres
--

CREATE FUNCTION itv.get_all_bcht_positions() RETURNS TABLE(inspection_gid integer, id_reg_ent text, id_reg_sor text, x double precision, y double precision, sens_ecoul text, type_obs text, fam_obs text, code_obs text, libel_obs text, orientatio text, geom public.geometry)
    LANGUAGE plpgsql
    AS $$
            DECLARE
                inspection_id integer;
            BEGIN
                FOR inspection_id IN
                    SELECT DISTINCT gid
                    FROM itv.inspection
                LOOP
                    RETURN QUERY
                    SELECT * FROM itv.get_bcht_positions(inspection_id);
                END LOOP;
            END;
            $$;


ALTER FUNCTION itv.get_all_bcht_positions() OWNER TO postgres;

--
-- TOC entry 937 (class 1255 OID 23669)
-- Name: get_all_defect_positions(); Type: FUNCTION; Schema: itv; Owner: postgres
--

CREATE FUNCTION itv.get_all_defect_positions() RETURNS TABLE(inspection_gid integer, id_reg_ent text, id_reg_sor text, id_troncon text, metrage numeric, x double precision, y double precision, n_passage text, sens_ecoul text, type_obs text, fam_obs text, code_obs text, libel_obs text, quan_charg text, rmq_obs text, orientatio text, precipitat text, photo text, video text, video_tps text, date_obs text, code_insee character varying, geom public.geometry)
    LANGUAGE plpgsql
    AS $$
            DECLARE
                inspection_id integer;
            BEGIN
                FOR inspection_id IN
                    SELECT DISTINCT gid
                    FROM itv.inspection
                LOOP
                    RETURN QUERY
                    SELECT * FROM itv.get_defect_positions(inspection_id);
                END LOOP;
            END;
            $$;


ALTER FUNCTION itv.get_all_defect_positions() OWNER TO postgres;

--
-- TOC entry 899 (class 1255 OID 23670)
-- Name: get_all_inspection_data(); Type: FUNCTION; Schema: itv; Owner: postgres
--

CREATE FUNCTION itv.get_all_inspection_data() RETURNS TABLE(inspection_gid integer, nature_res character varying, type_eau character varying, date_deb date, date_fin date, entreprise text, longueur numeric, nom_plan text, nom_rapport text, nom_txt text, remarques text, geom public.geometry)
    LANGUAGE plpgsql
    AS $$
            DECLARE
                inspection_id integer;
            BEGIN
                FOR inspection_id IN
                    SELECT DISTINCT gid
                    FROM itv.inspection
                LOOP
                    RETURN QUERY
                    SELECT * FROM itv.get_inspection_data(inspection_id);
                END LOOP;
            END;
            $$;


ALTER FUNCTION itv.get_all_inspection_data() OWNER TO postgres;

--
-- TOC entry 693 (class 1255 OID 23671)
-- Name: get_bcht_positions(integer); Type: FUNCTION; Schema: itv; Owner: postgres
--

CREATE FUNCTION itv.get_bcht_positions(inspection_gid_input integer) RETURNS TABLE(inspection_gid integer, id_reg_ent text, id_reg_sor text, x double precision, y double precision, sens_ecoul text, type_obs text, fam_obs text, code_obs text, libel_obs text, orientatio text, geom public.geometry)
    LANGUAGE plpgsql
    AS $$
            DECLARE
                coll_table text;
				coll_gid_column text;
                reg_table text;
				reg_gid_column text;
                sql_query text;
            BEGIN
                -- Récupérer les noms des tables depuis itv.inspection
                SELECT shp_coll_table, shp_reg_table INTO coll_table, reg_table
                FROM itv.inspection
                WHERE gid = inspection_gid_input;
				
				-- Déterminer la colonne à utiliser pour la table de collecte
				SELECT column_name INTO coll_gid_column
				FROM information_schema.columns
				WHERE table_schema = 'itv' AND table_name = coll_table AND column_name IN ('numero', 'ident')
				LIMIT 1;

				-- Déterminer la colonne à utiliser pour la table de regard
				SELECT column_name INTO reg_gid_column
				FROM information_schema.columns
				WHERE table_schema = 'itv' AND table_name = reg_table AND column_name IN ('numero', 'ident')
				LIMIT 1;

                -- Construire la requête SQL dynamique
                sql_query := format('
                    WITH inspection_data AS (
                        SELECT
                            v_itv_details.inspection_gid,
                            v_itv_details.id_reg_ent::text,
                            v_itv_details.id_reg_sor::text,
                            v_itv_details.id_troncon::text,
                            v_itv_details.metrage::numeric,
                            v_itv_details.n_passage::text,
                            v_itv_details.sens_ecoul::text,
                            v_itv_details.type_obs::text,
                            v_itv_details.fam_obs::text,
                            v_itv_details.code_obs::text,
                            v_itv_details.libel_obs::text,
                            v_itv_details.quan_charg::text,
                            v_itv_details.rmq_obs::text,
                            v_itv_details.orientatio::text,
                            v_itv_details.precipitat::text,
                            v_itv_details.photo::text,
                            v_itv_details.video::text,
                            v_itv_details.video_tps::text,
                            v_itv_details.date_obs::text,
                            ST_LineMerge(reseau.geom) AS troncon_geom,
                            regard_ent.geom AS regard_entrant_geom,
                            regard_sor.geom AS regard_sortant_geom
                        FROM
                            itv.v_itv_details
						JOIN
							itv.ids_coll ids_reseau ON ids_reseau.id_itv = v_itv_details.id_troncon
						JOIN
							itv.ids_reg ids_regard_ent ON ids_regard_ent.id_itv = v_itv_details.id_reg_ent
						JOIN
							itv.ids_reg ids_regard_sor ON ids_regard_sor.id_itv = v_itv_details.id_reg_sor
                        JOIN
                            itv.%I reseau ON reseau.%I = ids_reseau.id_sig
                        JOIN
                            itv.%I regard_ent ON regard_ent.%I = ids_regard_ent.id_sig
                        JOIN
                            itv.%I regard_sor ON regard_sor.%I = ids_regard_sor.id_sig
                        WHERE
                            v_itv_details.inspection_gid = %L
                            AND reseau.geom IS NOT NULL
                            AND regard_ent.geom IS NOT NULL
                            AND regard_sor.geom IS NOT NULL
                            AND fam_obs LIKE ''BCA''::text
                    ),
                    inspection_with_direction AS (
                        SELECT
                            *,
                            CASE
                                WHEN ST_Distance(ST_StartPoint(troncon_geom), regard_entrant_geom) < ST_Distance(ST_StartPoint(troncon_geom), regard_sortant_geom)
                                THEN ''forward''
                                ELSE ''reverse''
                            END AS direction
                        FROM
                            inspection_data
                    ),
                    bcht_positions AS (
                        SELECT
                            *,
                            CASE
                                WHEN direction = ''forward''
                                THEN ST_LineInterpolatePoint(troncon_geom, LEAST(metrage, ST_Length(troncon_geom)) / ST_Length(troncon_geom))::geometry(Point, 2154)
                                ELSE ST_LineInterpolatePoint(ST_Reverse(troncon_geom), LEAST(metrage, ST_Length(troncon_geom)) / ST_Length(troncon_geom))::geometry(Point, 2154)
                            END AS geom
                        FROM
                            inspection_with_direction
                    )
                    SELECT DISTINCT
                        inspection_gid,
                        id_reg_ent,
                        id_reg_sor,
                        ST_X(geom) AS x, -- Extraction de la coordonnée X
                        ST_Y(geom) AS y,  -- Extraction de la coordonnée Y
                        sens_ecoul,
                        type_obs,
                        fam_obs,
                        code_obs AS code,
                        libel_obs AS libelle,
                        orientatio,
                        geom
                    FROM
                        bcht_positions;
                ', coll_table, coll_gid_column, reg_table, reg_gid_column, reg_table, reg_gid_column, inspection_gid_input);

                -- Exécuter la requête SQL dynamique
                RETURN QUERY EXECUTE sql_query;
            END;
            $$;


ALTER FUNCTION itv.get_bcht_positions(inspection_gid_input integer) OWNER TO postgres;

--
-- TOC entry 506 (class 1255 OID 23672)
-- Name: get_defect_positions(integer); Type: FUNCTION; Schema: itv; Owner: postgres
--

CREATE FUNCTION itv.get_defect_positions(inspection_gid_input integer) RETURNS TABLE(inspection_gid integer, id_reg_ent text, id_reg_sor text, id_troncon text, metrage numeric, x double precision, y double precision, n_passage text, sens_ecoul text, type_obs text, fam_obs text, code_obs text, libel_obs text, quan_charg text, rmq_obs text, orientatio text, precipitat text, photo text, video text, video_tps text, date_obs text, code_insee character varying, geom public.geometry)
    LANGUAGE plpgsql
    AS $$
            DECLARE
                coll_table text;
				coll_gid_column text;
                reg_table text;
				reg_gid_column text;
                sql_query text;
            BEGIN
                -- Récupérer les noms des tables depuis itv.inspection
                SELECT shp_coll_table, shp_reg_table INTO coll_table, reg_table
                FROM itv.inspection
                WHERE gid = inspection_gid_input;
				
				-- Déterminer la colonne à utiliser pour la table de collecte
				SELECT column_name INTO coll_gid_column
				FROM information_schema.columns
				WHERE table_schema = 'itv' AND table_name = coll_table AND column_name IN ('numero', 'ident')
				LIMIT 1;

				-- Déterminer la colonne à utiliser pour la table de regard
				SELECT column_name INTO reg_gid_column
				FROM information_schema.columns
				WHERE table_schema = 'itv' AND table_name = reg_table AND column_name IN ('numero', 'ident')
				LIMIT 1;

                -- Construire la requête SQL dynamique
                sql_query := format('
                    WITH inspection_data AS (
                        SELECT
                            v_itv_details.inspection_gid,
                            v_itv_details.id_reg_ent::text,
                            v_itv_details.id_reg_sor::text,
                            v_itv_details.id_troncon::text,
                            v_itv_details.metrage::numeric,
                            v_itv_details.n_passage::text,
                            v_itv_details.sens_ecoul::text,
                            v_itv_details.type_obs::text,
                            v_itv_details.fam_obs::text,
                            v_itv_details.code_obs::text,
                            v_itv_details.libel_obs::text,
                            v_itv_details.quan_charg::text,
                            v_itv_details.rmq_obs::text,
                            v_itv_details.orientatio::text,
                            v_itv_details.precipitat::text,
                            v_itv_details.photo::text,
                            v_itv_details.video::text,
                            v_itv_details.video_tps::text,
                            v_itv_details.date_obs::text,
                            ST_LineMerge(reseau.geom) AS troncon_geom,
                            regard_ent.geom AS regard_entrant_geom,
                            regard_sor.geom AS regard_sortant_geom
                        FROM
                            itv.v_itv_details
						JOIN
							itv.ids_coll ids_reseau ON ids_reseau.id_itv = v_itv_details.id_troncon AND ids_reseau.id_sig IS NOT NULL
						JOIN
							itv.ids_reg ids_regard_ent ON ids_regard_ent.id_itv = v_itv_details.id_reg_ent AND ids_regard_ent.id_sig IS NOT NULL
						JOIN
							itv.ids_reg ids_regard_sor ON ids_regard_sor.id_itv = v_itv_details.id_reg_sor AND ids_regard_sor.id_sig IS NOT NULL
                        JOIN
                            itv.%I reseau ON reseau.%I = ids_reseau.id_sig
                        JOIN
                            itv.%I regard_ent ON regard_ent.%I = ids_regard_ent.id_sig
                        JOIN
                            itv.%I regard_sor ON regard_sor.%I = ids_regard_sor.id_sig
                        WHERE
                            v_itv_details.inspection_gid = %L
                            AND reseau.geom IS NOT NULL
                            AND regard_ent.geom IS NOT NULL
                            AND regard_sor.geom IS NOT NULL
                            AND fam_obs !~~ ''BCA''::text
                    ),
                    inspection_with_direction AS (
                        SELECT
                            *,
                            CASE
                                WHEN ST_Distance(ST_StartPoint(troncon_geom), regard_entrant_geom) < ST_Distance(ST_StartPoint(troncon_geom), regard_sortant_geom)
                                THEN ''forward''
                                ELSE ''reverse''
                            END AS direction
                        FROM
                            inspection_data
                    ),
                    defect_positions AS (
                        SELECT
                            *,
                            CASE
                                WHEN direction = ''forward''
                                THEN ST_LineInterpolatePoint(troncon_geom, LEAST(metrage, ST_Length(troncon_geom)) / ST_Length(troncon_geom))::geometry(Point, 2154)
                                ELSE ST_LineInterpolatePoint(ST_Reverse(troncon_geom), LEAST(metrage, ST_Length(troncon_geom)) / ST_Length(troncon_geom))::geometry(Point, 2154)
                            END AS geom
                        FROM
                            inspection_with_direction
                    ),
                    defect_positions_with_code_insee AS (
                        SELECT
                            dp.*,
                            c.insee_com
                        FROM
                            defect_positions dp
                        LEFT JOIN
                            itv.commune c ON ST_Intersects(dp.geom, c.geom)
                    )
                    SELECT DISTINCT
                        inspection_gid,
                        id_reg_ent,
                        id_reg_sor,
                        id_troncon,
                        metrage,
                        ST_X(geom) AS x, -- Extraction de la coordonnée X
                        ST_Y(geom) AS y,  -- Extraction de la coordonnée Y
                        n_passage,
                        sens_ecoul,
                        type_obs,
                        fam_obs,
                        code_obs,
                        libel_obs,
                        quan_charg,
                        rmq_obs,
                        orientatio,
                        precipitat,
                        photo,
                        video,
                        video_tps,
                        date_obs,
                        insee_com AS code_insee,
                        geom
                    FROM
                        defect_positions_with_code_insee;
                ', coll_table, coll_gid_column, reg_table, reg_gid_column, reg_table, reg_gid_column, inspection_gid_input);

                -- Exécuter la requête SQL dynamique
                RETURN QUERY EXECUTE sql_query;
            END;
            
$$;


ALTER FUNCTION itv.get_defect_positions(inspection_gid_input integer) OWNER TO postgres;

--
-- TOC entry 364 (class 1255 OID 23674)
-- Name: get_id_sig(text, character varying, integer); Type: FUNCTION; Schema: itv; Owner: postgres
--

CREATE FUNCTION itv.get_id_sig(table_name text, id_itv character varying, inspection integer) RETURNS text
    LANGUAGE plpgsql
    AS $_$
DECLARE
    id_sig text;
BEGIN
    EXECUTE format('SELECT id_sig FROM itv.%I WHERE id_itv = $1 AND inspection_gid = $2 LIMIT 1', table_name)
    INTO id_sig
    USING id_itv, inspection;

    RETURN id_sig;
END;
$_$;


ALTER FUNCTION itv.get_id_sig(table_name text, id_itv character varying, inspection integer) OWNER TO postgres;

--
-- TOC entry 314 (class 1255 OID 23675)
-- Name: get_inspection_data(integer); Type: FUNCTION; Schema: itv; Owner: postgres
--

CREATE FUNCTION itv.get_inspection_data(inspection_gid_input integer) RETURNS TABLE(inspection_gid integer, nature_res character varying, type_eau character varying, date_deb date, date_fin date, entreprise text, longueur numeric, nom_plan text, nom_rapport text, nom_txt text, remarques text, geom public.geometry)
    LANGUAGE plpgsql
    AS $$
            DECLARE
                coll_table text;
                reg_table text;
				coll_gid_column text;
    			reg_gid_column text;
                geom_coll geometry;
                geom_reg geometry;
            BEGIN
                -- Récupérer les noms des tables depuis itv.inspection
                SELECT shp_coll_table, shp_reg_table INTO coll_table, reg_table
                FROM itv.inspection
                WHERE gid = inspection_gid_input;
				
				-- Déterminer la colonne à utiliser pour la table de collecte
				SELECT column_name INTO coll_gid_column
				FROM information_schema.columns
				WHERE table_schema = 'itv' AND table_name = coll_table AND column_name IN ('numero', 'ident')
				LIMIT 1;

				-- Déterminer la colonne à utiliser pour la table de regard
				SELECT column_name INTO reg_gid_column
				FROM information_schema.columns
				WHERE table_schema = 'itv' AND table_name = reg_table AND column_name IN ('numero', 'ident')
				LIMIT 1;

                -- Construire et exécuter la requête dynamique pour la géométrie du réseau de collecte
                EXECUTE format('
                    SELECT st_union(geom) 
                    FROM itv.%I 
                    WHERE %I::text IN (
                        SELECT v_itv_physiq_coll.id_sig
                        FROM itv.v_itv_physiq_coll
                        WHERE v_itv_physiq_coll.id_troncon::text IN (
                            SELECT v_itv_details.id_troncon
                            FROM itv.v_itv_details
                            WHERE v_itv_details.inspection_gid = %L
                        )
                    )', coll_table, coll_gid_column, inspection_gid_input) INTO geom_coll;

                -- Construire et exécuter la requête dynamique pour la géométrie des points d'inspection
                EXECUTE format('
                    SELECT st_union(geom) 
                    FROM itv.%I 
                    WHERE %I::text IN (
                        SELECT v_itv_physiq_reg.id_sig
                        FROM itv.v_itv_physiq_reg
                        WHERE v_itv_physiq_reg.id_regard IN (
                            SELECT v_itv_details.id_reg_ent
                            FROM itv.v_itv_details
                            WHERE v_itv_details.inspection_gid = %L
                        ) OR v_itv_physiq_reg.id_regard IN (
                            SELECT v_itv_details.id_reg_sor
                            FROM itv.v_itv_details
                            WHERE v_itv_details.inspection_gid = %L
                        )
                    )', reg_table, reg_gid_column, inspection_gid_input, inspection_gid_input) INTO geom_reg;

				 -- Check if geom_reg is a point
				IF ST_GeometryType(geom_reg) = 'ST_Point' THEN
					geom_reg := ST_Buffer(geom_reg, 0.0001); -- Create a small polygon around the point
				END IF;
                -- Combiner les géométries et retourner le résultat
                geom := ST_Envelope(ST_Union(ARRAY[geom_coll, geom_reg]));

                -- Sélectionner les autres champs et retourner le résultat
                RETURN QUERY
                SELECT 
                    inspection.gid AS inspection_gid,
                    NULL::character varying(2) AS nature_res,
                    NULL::character varying(2) AS type_eau,
                    (SELECT min("B02_2"."ABF") AS max
                    FROM itv."B02" "B02_2",
                        itv.passage passage_2
                    WHERE passage_2.gid = "B02_2".passage_gid 
                    AND passage_2.inspection_gid = inspection.gid) AS date_deb,
                    (SELECT max("B02_1"."ABF") AS max
                    FROM itv."B02" "B02_1",
                        itv.passage passage_1
                    WHERE passage_1.gid = "B02_1".passage_gid 
                    AND passage_1.inspection_gid = inspection.gid) AS date_fin,
                    inspection.entreprise::text,
                    sum("B03"."ACG")::numeric AS longueur,
                    inspection.pdf_filename::text AS nom_plan,
                    inspection.pdf_filename::text AS nom_rapport,
                    inspection.file::text AS nom_txt,
                    string_agg("B04"."ADE"::text, ''::text) AS remarques,
                    geom::geometry(Polygon,2154) AS geom
                FROM 
                    itv."B01",
                    itv."B02",
                    itv."B03",
                    itv."B04",
                    itv.passage,
                    itv.inspection
                WHERE 
                    "B01".passage_gid = passage.gid 
                    AND "B02".passage_gid = passage.gid 
                    AND "B03".passage_gid = passage.gid 
                    AND "B04".passage_gid = passage.gid 
                    AND passage.inspection_gid = inspection.gid
                    AND inspection.gid = inspection_gid_input
                GROUP BY 
                    inspection.gid;
            END;
            $$;


ALTER FUNCTION itv.get_inspection_data(inspection_gid_input integer) OWNER TO postgres;

--
-- TOC entry 522 (class 1255 OID 23676)
-- Name: set_id_sig(integer); Type: FUNCTION; Schema: itv; Owner: postgres
--

CREATE FUNCTION itv.set_id_sig(inspection_gid_input integer) RETURNS void
    LANGUAGE plpgsql
    AS $_$
DECLARE
	coll_table text;
	reg_table text;
	coll_gid_column text;
	reg_gid_column text;
BEGIN

	-- Récupérer les noms des tables depuis itv.inspection
	SELECT shp_coll_table, shp_reg_table INTO coll_table, reg_table
	FROM itv.inspection
	WHERE gid = inspection_gid_input;
	
	-- Déterminer la colonne à utiliser pour la table de collecte
	SELECT column_name INTO coll_gid_column
	FROM information_schema.columns
	WHERE table_schema = 'itv' AND table_name = coll_table AND column_name IN ('numero', 'ident')
	LIMIT 1;

	-- Déterminer la colonne à utiliser pour la table de regard
	SELECT column_name INTO reg_gid_column
	FROM information_schema.columns
	WHERE table_schema = 'itv' AND table_name = reg_table AND column_name IN ('numero', 'ident')
	LIMIT 1;

    -- Insérer les données dans la table ids_reg
	EXECUTE format('
        INSERT INTO itv.ids_reg (inspection_gid, id_itv, id_sig)
        SELECT
            $1,
            v_itv_physiq_reg.id_regard,
            (SELECT %I FROM itv.%I WHERE %I LIKE v_itv_physiq_reg.id_regard LIMIT 1)
        FROM itv.v_itv_physiq_reg
        WHERE inspection_gid = $1
        ON CONFLICT (inspection_gid, id_itv) DO UPDATE
        SET id_sig = COALESCE(EXCLUDED.id_sig, itv.ids_reg.id_sig)
	', reg_gid_column, reg_table, reg_gid_column)
	USING inspection_gid_input;
	
	-- Insérer les données dans la table ids_reg
	EXECUTE format('
        INSERT INTO itv.ids_coll (inspection_gid, id_itv, id_sig)
        SELECT
            $1,
            v_itv_physiq_coll.id_troncon,
            (SELECT %I FROM itv.%I WHERE %I LIKE v_itv_physiq_coll.id_troncon LIMIT 1)
        FROM itv.v_itv_physiq_coll
        WHERE inspection_gid = $1
        ON CONFLICT (inspection_gid, id_itv) DO UPDATE
        SET id_sig = COALESCE(EXCLUDED.id_sig, itv.ids_coll.id_sig)
	', coll_gid_column, coll_table, coll_gid_column)
	USING inspection_gid_input;
	
    -- Insérer les valeurs NULL pour les id_itv sans correspondance
    EXECUTE format('
        INSERT INTO itv.ids_reg (inspection_gid, id_itv, id_sig)
        SELECT
            $1,
            v_itv_physiq_reg.id_regard,
            NULL
        FROM itv.v_itv_physiq_reg
        WHERE inspection_gid = $1
        AND NOT EXISTS (
            SELECT 1 FROM itv.ids_reg
            WHERE inspection_gid = $1 AND id_itv = v_itv_physiq_reg.id_regard
        )
    ')
    USING inspection_gid_input;

    EXECUTE format('
        INSERT INTO itv.ids_coll (inspection_gid, id_itv, id_sig)
        SELECT
            $1,
            v_itv_physiq_coll.id_troncon,
            NULL
        FROM itv.v_itv_physiq_coll
        WHERE inspection_gid = $1
        AND NOT EXISTS (
            SELECT 1 FROM itv.ids_coll
            WHERE inspection_gid = $1 AND id_itv = v_itv_physiq_coll.id_troncon
        )
    ')
    USING inspection_gid_input;
	
END;
$_$;


ALTER FUNCTION itv.set_id_sig(inspection_gid_input integer) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 224 (class 1259 OID 23677)
-- Name: B01; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv."B01" (
    gid integer NOT NULL,
    "AAA" character varying(15),
    "AAB" character varying(15),
    "AAC" character varying(15),
    "AAD" character varying(15),
    "AAE" character varying(15),
    "AAF" character varying(15),
    "AAG" character varying(15),
    "AAH" character varying(15),
    "AAI" character varying(15),
    "AAJ" character varying(100),
    "AAK" character varying(1),
    "AAL" character varying(1),
    "AAM" character varying(100),
    "AAN" character varying(100),
    "AAO" character varying(15),
    "AAP" character varying(15),
    "AAQ" character varying(1),
    "AAT" character varying(15),
    "AAU" character varying(15),
    "AAV" character varying(1),
    passage_gid integer
);


ALTER TABLE itv."B01" OWNER TO postgres;

--
-- TOC entry 5898 (class 0 OID 0)
-- Dependencies: 224
-- Name: TABLE "B01"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON TABLE itv."B01" IS 'Lieu d''inspection';


--
-- TOC entry 5899 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAA"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAA" IS 'Référence de tronçon (ID Tronçon)';


--
-- TOC entry 5900 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAB"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAB" IS 'Référence du noeud de départ (ID Regard)';


--
-- TOC entry 5901 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAC"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAC" IS 'Coordonnées du noeud de départ';


--
-- TOC entry 5902 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAD"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAD" IS 'Référence du nœud 1 (ID regard)';


--
-- TOC entry 5903 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAE"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAE" IS 'Coordonnées du nœud 1';


--
-- TOC entry 5904 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAF"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAF" IS 'Référence du nœud 2 (ID regard)';


--
-- TOC entry 5905 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAG"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAG" IS 'Coordonnées du nœud 2';


--
-- TOC entry 5906 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAH"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAH" IS 'Emplacement longitudinal du
            point de départ de la canalisation
            latérale';


--
-- TOC entry 5907 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAI"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAI" IS 'Emplacement circonférentiel du
            point de départ de la canalisation
            latérale (Position horaire)';


--
-- TOC entry 5908 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAJ"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAJ" IS 'Emplacement';


--
-- TOC entry 5909 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAK"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAK" IS 'Sens de l''écoulement';


--
-- TOC entry 5910 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAL"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAL" IS 'Type d''emplacement';


--
-- TOC entry 5911 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAM"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAM" IS 'Organisation ou entité responsable';


--
-- TOC entry 5912 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAN"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAN" IS 'Commune';


--
-- TOC entry 5913 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAO"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAO" IS 'Code de localisation ou numéro de zone (Quartier)';


--
-- TOC entry 5914 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAP"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAP" IS 'Nom du réseau d''assainissement';


--
-- TOC entry 5915 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAQ"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAQ" IS 'Propriété foncière';


--
-- TOC entry 5916 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAT"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAT" IS 'Référence du noeud 3 (ID Regard)';


--
-- TOC entry 5917 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAU"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAU" IS 'Coordonnées du noeud 3';


--
-- TOC entry 5918 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN "B01"."AAV"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B01"."AAV" IS 'Point de départ de l''inspection
            latérale';


--
-- TOC entry 225 (class 1259 OID 23682)
-- Name: B01_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv."B01_gid_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv."B01_gid_seq" OWNER TO postgres;

--
-- TOC entry 5919 (class 0 OID 0)
-- Dependencies: 225
-- Name: B01_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv."B01_gid_seq" OWNED BY itv."B01".gid;


--
-- TOC entry 226 (class 1259 OID 23683)
-- Name: B02; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv."B02" (
    gid integer NOT NULL,
    "ABA" character varying(50),
    "ABB" character varying(1),
    "ABC" character varying(1),
    "ABD" character varying(1),
    "ABE" character varying(1),
    "ABF" date,
    "ABG" character varying(50),
    "ABH" character varying(50),
    "ABI" character varying(50),
    "ABJ" character varying(50),
    "ABK" character varying(50),
    "ABL" character varying(50),
    "ABM" character varying(50),
    "ABN" character varying(50),
    "ABO" character varying(15),
    "ABP" character varying(50),
    "ABQ" double precision,
    "ABR" character varying(15),
    "ABS" character varying(15),
    "ABT" character varying(1),
    passage_gid integer
);


ALTER TABLE itv."B02" OWNER TO postgres;

--
-- TOC entry 5920 (class 0 OID 0)
-- Dependencies: 226
-- Name: TABLE "B02"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON TABLE itv."B02" IS 'Détails concernant l''inspection';


--
-- TOC entry 5921 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABA"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABA" IS 'Norme utilisée';


--
-- TOC entry 5922 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABB"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABB" IS 'Système de codage initial';


--
-- TOC entry 5923 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABC"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABC" IS 'Point de référence longitudinal';


--
-- TOC entry 5924 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABD"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABD" IS 'Non utilisé';


--
-- TOC entry 5925 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABE"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABE" IS 'Méthode de l''inspection';


--
-- TOC entry 5926 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABF"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABF" IS 'Date de l’inspection';


--
-- TOC entry 5927 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABG"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABG" IS 'Heure l''inspection';


--
-- TOC entry 5928 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABH"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABH" IS 'Nom de l''inspecteur';


--
-- TOC entry 5929 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABI"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABI" IS 'Référence de fonction de l’inspecteur';


--
-- TOC entry 5930 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABJ"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABJ" IS 'Référence de fonction de l’inspecteur';


--
-- TOC entry 5931 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABK"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABK" IS 'Support de stockage des images vidéo';


--
-- TOC entry 5932 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABL"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABL" IS 'Format de stockage des photographies';


--
-- TOC entry 5933 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABM"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABM" IS 'Système de position sur la bande vidéo';


--
-- TOC entry 5934 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABN"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABN" IS 'Référence de photographie';


--
-- TOC entry 5935 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABO"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABO" IS 'Référence de vidéo';


--
-- TOC entry 5936 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABP"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABP" IS 'Objet de l''inspection';


--
-- TOC entry 5937 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABQ"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABQ" IS 'Étendue d’inspection prévue';


--
-- TOC entry 5938 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABR"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABR" IS 'Format d''images vidéo';


--
-- TOC entry 5939 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABS"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABS" IS 'Nom de fichier d''images vidéo';


--
-- TOC entry 5940 (class 0 OID 0)
-- Dependencies: 226
-- Name: COLUMN "B02"."ABT"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B02"."ABT" IS 'Étape de l’inspection';


--
-- TOC entry 227 (class 1259 OID 23688)
-- Name: B02_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv."B02_gid_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv."B02_gid_seq" OWNER TO postgres;

--
-- TOC entry 5941 (class 0 OID 0)
-- Dependencies: 227
-- Name: B02_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv."B02_gid_seq" OWNED BY itv."B02".gid;


--
-- TOC entry 228 (class 1259 OID 23689)
-- Name: B03; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv."B03" (
    gid integer NOT NULL,
    "ACA" character varying(1),
    "ACB" double precision,
    "ACC" character varying(50),
    "ACD" character varying(3),
    "ACE" character varying(5),
    "ACF" character varying(5),
    "ACG" double precision,
    "ACH" double precision,
    "ACI" character varying(50),
    "ACJ" character varying(1),
    "ACK" character varying(1),
    "ACL" character varying(1),
    "ACM" character varying(1),
    "ACN" character varying(2),
    passage_gid integer
);


ALTER TABLE itv."B03" OWNER TO postgres;

--
-- TOC entry 5942 (class 0 OID 0)
-- Dependencies: 228
-- Name: TABLE "B03"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON TABLE itv."B03" IS 'Détails de la canalisation';


--
-- TOC entry 5943 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACA"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACA" IS 'Forme (canalisation)';


--
-- TOC entry 5944 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACB"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACB" IS 'Hauteur (mm)';


--
-- TOC entry 5945 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACC"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACC" IS 'Largeur (mm)';


--
-- TOC entry 5946 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACD"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACD" IS 'Matérieu constitutif (structure du collecteur)';


--
-- TOC entry 5947 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACE"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACE" IS 'Type de revêtement';


--
-- TOC entry 5948 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACF"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACF" IS 'Matériau de revêtement';


--
-- TOC entry 5949 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACG"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACG" IS 'Longueur unitaire de conduite';


--
-- TOC entry 5950 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACH"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACH" IS 'Profondeur du noeud de départ';


--
-- TOC entry 5951 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACI"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACI" IS 'Profondeur du noeud d''arrivé';


--
-- TOC entry 5952 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACJ"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACJ" IS 'Type de branchement ou de collecteur';


--
-- TOC entry 5953 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACK"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACK" IS 'Utilisation du branchement ou du collecteur';


--
-- TOC entry 5954 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACL"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACL" IS 'Position stratégique';


--
-- TOC entry 5955 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACM"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACM" IS 'Nettoyage préalable';


--
-- TOC entry 5956 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN "B03"."ACN"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B03"."ACN" IS 'Année de mise en service';


--
-- TOC entry 229 (class 1259 OID 23692)
-- Name: B03_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv."B03_gid_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv."B03_gid_seq" OWNER TO postgres;

--
-- TOC entry 5957 (class 0 OID 0)
-- Dependencies: 229
-- Name: B03_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv."B03_gid_seq" OWNED BY itv."B03".gid;


--
-- TOC entry 230 (class 1259 OID 23693)
-- Name: B04; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv."B04" (
    gid integer NOT NULL,
    "ADA" character varying(1),
    "ADB" character varying(1),
    "ADC" character varying(1),
    "ADD" character varying(1),
    "ADE" character varying(255),
    passage_gid integer
);


ALTER TABLE itv."B04" OWNER TO postgres;

--
-- TOC entry 5958 (class 0 OID 0)
-- Dependencies: 230
-- Name: TABLE "B04"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON TABLE itv."B04" IS 'Autres informations';


--
-- TOC entry 5959 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN "B04"."ADA"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B04"."ADA" IS 'Précipitations';


--
-- TOC entry 5960 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN "B04"."ADB"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B04"."ADB" IS 'Température';


--
-- TOC entry 5961 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN "B04"."ADC"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B04"."ADC" IS 'Régulation de débit';


--
-- TOC entry 5962 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN "B04"."ADD"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B04"."ADD" IS 'N''est pas utilisé';


--
-- TOC entry 5963 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN "B04"."ADE"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."B04"."ADE" IS 'Remarques générales';


--
-- TOC entry 231 (class 1259 OID 23696)
-- Name: B04_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv."B04_gid_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv."B04_gid_seq" OWNER TO postgres;

--
-- TOC entry 5964 (class 0 OID 0)
-- Dependencies: 231
-- Name: B04_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv."B04_gid_seq" OWNED BY itv."B04".gid;


--
-- TOC entry 232 (class 1259 OID 23697)
-- Name: C; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv."C" (
    gid integer NOT NULL,
    "I" double precision,
    "J" character varying(3),
    "A" character varying(3),
    "B" character varying(2),
    "C" character varying(2),
    "D" character varying(10),
    "E" character varying(5),
    "F" character varying(100),
    "G" character varying(5),
    "H" character varying(5),
    "K" character varying(1),
    "L" character varying(15),
    "M" character varying(100),
    "N" character varying(50),
    passage_gid integer
);


ALTER TABLE itv."C" OWNER TO postgres;

--
-- TOC entry 5965 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."I"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."I" IS 'Longueur inspectée (m)';


--
-- TOC entry 5966 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."J"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."J" IS 'Code de défaut continu
            -- incertain';


--
-- TOC entry 5967 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."A"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."A" IS 'Code principal';


--
-- TOC entry 5968 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."B"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."B" IS 'Caractérisation 1';


--
-- TOC entry 5969 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."C"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."C" IS 'Caractérisation 2';


--
-- TOC entry 5970 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."D"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."D" IS 'Quantification 1';


--
-- TOC entry 5971 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."E"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."E" IS 'Quantification 2';


--
-- TOC entry 5972 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."F"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."F" IS 'Remarque sur l’observation';


--
-- TOC entry 5973 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."G"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."G" IS 'Emplacement circonférentiel 1';


--
-- TOC entry 5974 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."H"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."H" IS 'Emplacement circonférentiel 2';


--
-- TOC entry 5975 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."K"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."K" IS 'Observation au niveau d''un assemblage';


--
-- TOC entry 5976 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."L"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."L" IS 'N''est pas utilisé';


--
-- TOC entry 5977 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."M"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."M" IS 'Réf. photo';


--
-- TOC entry 5978 (class 0 OID 0)
-- Dependencies: 232
-- Name: COLUMN "C"."N"; Type: COMMENT; Schema: itv; Owner: postgres
--

COMMENT ON COLUMN itv."C"."N" IS 'Réf. vidéo';


--
-- TOC entry 233 (class 1259 OID 23700)
-- Name: C_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv."C_gid_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv."C_gid_seq" OWNER TO postgres;

--
-- TOC entry 5979 (class 0 OID 0)
-- Dependencies: 233
-- Name: C_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv."C_gid_seq" OWNED BY itv."C".gid;


--
-- TOC entry 234 (class 1259 OID 23701)
-- Name: commune; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv.commune (
    gid integer NOT NULL,
    id character varying(24),
    nom character varying(50),
    nom_m character varying(50),
    insee_com character varying(5),
    statut character varying(26),
    population numeric(8,0),
    insee_can character varying(5),
    insee_arr character varying(2),
    insee_dep character varying(3),
    insee_reg character varying(2),
    siren_epci character varying(20),
    geom public.geometry(MultiPolygon,2154)
);


ALTER TABLE itv.commune OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 23706)
-- Name: commune_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv.commune_gid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv.commune_gid_seq OWNER TO postgres;

--
-- TOC entry 5980 (class 0 OID 0)
-- Dependencies: 235
-- Name: commune_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv.commune_gid_seq OWNED BY itv.commune.gid;


--
-- TOC entry 236 (class 1259 OID 23707)
-- Name: ids_coll; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv.ids_coll (
    gid integer NOT NULL,
    inspection_gid integer,
    id_itv character varying(50),
    id_sig character varying(50)
);


ALTER TABLE itv.ids_coll OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 23710)
-- Name: correspondance_coll_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv.correspondance_coll_gid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv.correspondance_coll_gid_seq OWNER TO postgres;

--
-- TOC entry 5981 (class 0 OID 0)
-- Dependencies: 237
-- Name: correspondance_coll_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv.correspondance_coll_gid_seq OWNED BY itv.ids_coll.gid;


--
-- TOC entry 238 (class 1259 OID 23711)
-- Name: ids_reg; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv.ids_reg (
    gid integer NOT NULL,
    inspection_gid integer,
    id_itv character varying(50),
    id_sig character varying(50)
);


ALTER TABLE itv.ids_reg OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 23714)
-- Name: correspondance_reg_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv.correspondance_reg_gid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv.correspondance_reg_gid_seq OWNER TO postgres;

--
-- TOC entry 5982 (class 0 OID 0)
-- Dependencies: 239
-- Name: correspondance_reg_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv.correspondance_reg_gid_seq OWNED BY itv.ids_reg.gid;


--
-- TOC entry 240 (class 1259 OID 23715)
-- Name: inspection; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv.inspection (
    gid integer NOT NULL,
    file character varying(255),
    "A1" character varying(50),
    "A2" character varying(5),
    "A3" character varying(2),
    "A4" character varying(1),
    "A5" character varying(1),
    "A6" character varying(5),
    shp_reg character varying(255),
    shp_coll character varying(255),
    entreprise character varying(100),
    pdf_filename character varying(255),
    shp_reg_table character varying(255),
    shp_coll_table character varying(255),
    created_by integer
);


ALTER TABLE itv.inspection OWNER TO postgres;

--
-- TOC entry 241 (class 1259 OID 23720)
-- Name: inspection_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv.inspection_gid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv.inspection_gid_seq OWNER TO postgres;

--
-- TOC entry 5983 (class 0 OID 0)
-- Dependencies: 241
-- Name: inspection_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv.inspection_gid_seq OWNED BY itv.inspection.gid;


--
-- TOC entry 242 (class 1259 OID 23721)
-- Name: passage; Type: TABLE; Schema: itv; Owner: postgres
--

CREATE TABLE itv.passage (
    gid integer NOT NULL,
    n_passage integer,
    inspection_gid integer
);


ALTER TABLE itv.passage OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 23724)
-- Name: passage_gid_seq; Type: SEQUENCE; Schema: itv; Owner: postgres
--

CREATE SEQUENCE itv.passage_gid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE itv.passage_gid_seq OWNER TO postgres;

--
-- TOC entry 5984 (class 0 OID 0)
-- Dependencies: 243
-- Name: passage_gid_seq; Type: SEQUENCE OWNED BY; Schema: itv; Owner: postgres
--

ALTER SEQUENCE itv.passage_gid_seq OWNED BY itv.passage.gid;


--
-- TOC entry 244 (class 1259 OID 23725)
-- Name: v_inspection; Type: VIEW; Schema: itv; Owner: postgres
--

CREATE VIEW itv.v_inspection AS
 SELECT inspection_gid,
    nature_res,
    type_eau,
    date_deb,
    date_fin,
    entreprise,
    longueur,
    nom_plan,
    nom_rapport,
    nom_txt,
    remarques,
    (geom)::public.geometry(Polygon,2154) AS geom
   FROM itv.get_all_inspection_data() get_all_inspection_data(inspection_gid, nature_res, type_eau, date_deb, date_fin, entreprise, longueur, nom_plan, nom_rapport, nom_txt, remarques, geom);


ALTER VIEW itv.v_inspection OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 23729)
-- Name: v_itv_details; Type: VIEW; Schema: itv; Owner: postgres
--

CREATE VIEW itv.v_itv_details AS
 SELECT row_number() OVER () AS gid,
    inspection.gid AS inspection_gid,
    passage.n_passage,
    "B01"."AAK" AS sens_ecoul,
    "B01"."AAB" AS id_reg_ent,
    "B01"."AAF" AS id_reg_sor,
    "B01"."AAA" AS id_troncon,
    NULL::text AS type_obs,
    "C"."A" AS fam_obs,
    concat("C"."A",
        CASE
            WHEN (("C"."B" IS NOT NULL) AND (("C"."B")::text <> ''::text)) THEN ('-'::text || ("C"."B")::text)
            ELSE ''::text
        END,
        CASE
            WHEN (("C"."C" IS NOT NULL) AND (("C"."C")::text <> ''::text)) THEN ('-'::text || ("C"."C")::text)
            ELSE ''::text
        END) AS code_obs,
    NULL::text AS libel_obs,
    "C"."D" AS quan_charg,
    "C"."F" AS rmq_obs,
    concat(
        CASE
            WHEN (("C"."G" IS NOT NULL) AND (("C"."G")::text <> ''::text)) THEN (lpad(("C"."G")::text, 2, '0'::text) || 'h'::text)
            ELSE ''::text
        END,
        CASE
            WHEN (("C"."H" IS NOT NULL) AND (("C"."H")::text <> ''::text) AND (("C"."G" IS NULL) OR (("C"."G")::text ~~ ''::text))) THEN (lpad(("C"."H")::text, 2, '0'::text) || 'h'::text)
            WHEN (("C"."H" IS NOT NULL) AND (("C"."H")::text <> ''::text) AND ("C"."G" IS NOT NULL) AND (("C"."G")::text <> ''::text)) THEN (('-'::text || lpad(("C"."H")::text, 2, '0'::text)) || 'h'::text)
            ELSE ''::text
        END) AS orientatio,
    "C"."I" AS metrage,
    "B04"."ADA" AS precipitat,
    "C"."M" AS photo,
    "B02"."ABS" AS video,
    "C"."N" AS video_tps,
    "B02"."ABF" AS date_obs
   FROM ((((((itv."B01"
     JOIN itv.passage ON (("B01".passage_gid = passage.gid)))
     JOIN itv.inspection ON ((passage.inspection_gid = inspection.gid)))
     JOIN itv."B02" ON (("B02".passage_gid = passage.gid)))
     JOIN itv."B03" ON (("B03".passage_gid = passage.gid)))
     JOIN itv."B04" ON (("B04".passage_gid = passage.gid)))
     JOIN itv."C" ON (("C".passage_gid = passage.gid)));


ALTER VIEW itv.v_itv_details OWNER TO postgres;

--
-- TOC entry 246 (class 1259 OID 23734)
-- Name: v_itv_details_bcht; Type: VIEW; Schema: itv; Owner: postgres
--

CREATE VIEW itv.v_itv_details_bcht AS
 SELECT row_number() OVER () AS id,
    inspection_gid,
    NULL::text AS id_bcht,
    x,
    y,
    code_obs AS code,
    libel_obs AS libelle,
    orientatio,
    sens_ecoul AS sens_inspe,
    NULL::text AS type_mat,
    NULL::text AS diametre,
    id_reg_ent,
    id_reg_sor,
    (geom)::public.geometry(Point,2154) AS geom
   FROM itv.get_all_bcht_positions() get_all_bcht_positions(inspection_gid, id_reg_ent, id_reg_sor, x, y, sens_ecoul, type_obs, fam_obs, code_obs, libel_obs, orientatio, geom);


ALTER VIEW itv.v_itv_details_bcht OWNER TO postgres;

--
-- TOC entry 247 (class 1259 OID 23738)
-- Name: v_itv_details_geom; Type: VIEW; Schema: itv; Owner: postgres
--

CREATE VIEW itv.v_itv_details_geom AS
 SELECT row_number() OVER () AS gid,
    inspection_gid,
    id_reg_ent,
    id_reg_sor,
    id_troncon,
    metrage,
    x,
    y,
    n_passage,
    sens_ecoul,
    type_obs,
    fam_obs,
    code_obs,
    libel_obs,
    quan_charg,
    rmq_obs,
    orientatio,
    precipitat,
    photo,
    video,
    video_tps,
    date_obs,
    code_insee,
    (geom)::public.geometry(Point,2154) AS geom
   FROM itv.get_all_defect_positions() get_all_defect_positions(inspection_gid, id_reg_ent, id_reg_sor, id_troncon, metrage, x, y, n_passage, sens_ecoul, type_obs, fam_obs, code_obs, libel_obs, quan_charg, rmq_obs, orientatio, precipitat, photo, video, video_tps, date_obs, code_insee, geom);


ALTER VIEW itv.v_itv_details_geom OWNER TO postgres;

--
-- TOC entry 248 (class 1259 OID 23743)
-- Name: v_itv_physiq_coll; Type: VIEW; Schema: itv; Owner: postgres
--

CREATE VIEW itv.v_itv_physiq_coll AS
 SELECT row_number() OVER () AS gid,
    inspection.gid AS inspection_gid,
    "B01"."AAA" AS id_troncon,
    NULL::text AS type_res,
        CASE
            WHEN (("B03"."ACD")::text = 'AP'::text) THEN '01'::text
            WHEN (("B03"."ACD")::text = 'AA'::text) THEN '02'::text
            WHEN (("B03"."ACD")::text = 'AH'::text) THEN '03'::text
            WHEN (("B03"."ACD")::text = 'AG'::text) THEN '04'::text
            WHEN (("B03"."ACD")::text = 'AM'::text) THEN '05'::text
            WHEN (("B03"."ACD")::text = 'AO'::text) THEN '06'::text
            WHEN (("B03"."ACD")::text = 'AN'::text) THEN '07'::text
            WHEN (("B03"."ACD")::text = 'AZ'::text) THEN '08'::text
            WHEN (("B03"."ACD")::text = 'AE'::text) THEN '09'::text
            WHEN (("B03"."ACD")::text = 'AV'::text) THEN '10'::text
            WHEN (("B03"."ACD")::text = 'AX'::text) THEN '11'::text
            WHEN (("B03"."ACD")::text = 'AL'::text) THEN '12'::text
            WHEN (("B03"."ACD")::text = 'AW'::text) THEN '13'::text
            WHEN (("B03"."ACD")::text = 'AK'::text) THEN '14'::text
            WHEN (("B03"."ACD")::text = 'Z'::text) THEN '15'::text
            WHEN (("B03"."ACD")::text = 'AU'::text) THEN '16'::text
            WHEN (("B03"."ACD")::text = 'AR'::text) THEN '17'::text
            ELSE '00'::text
        END AS type_mat,
        CASE
            WHEN (("B03"."ACC" IS NULL) OR (("B03"."ACC")::text = ''::text)) THEN "B03"."ACB"
            ELSE NULL::double precision
        END AS diam_nom,
        CASE
            WHEN (("B03"."ACC" IS NOT NULL) AND (("B03"."ACC")::text <> ''::text)) THEN "B03"."ACB"
            ELSE NULL::double precision
        END AS hauteur,
        CASE
            WHEN (("B03"."ACC" IS NOT NULL) AND (("B03"."ACC")::text <> ''::text)) THEN "B03"."ACC"
            ELSE NULL::character varying
        END AS largeur,
        CASE
            WHEN (("B03"."ACA")::text = 'B'::text) THEN '01'::text
            WHEN (("B03"."ACA")::text = 'A'::text) THEN '02'::text
            WHEN (("B03"."ACA")::text = 'D'::text) THEN '03'::text
            WHEN (("B03"."ACA")::text = ''::text) THEN '04'::text
            WHEN (("B03"."ACA")::text = ''::text) THEN '05'::text
            WHEN (("B03"."ACA")::text = ''::text) THEN '06'::text
            WHEN (("B03"."ACA")::text = 'F'::text) THEN '07'::text
            WHEN (("B03"."ACA")::text = ''::text) THEN '08'::text
            ELSE '00'::text
        END AS forme,
    itv.get_id_sig('ids_coll'::text, (("B01"."AAA")::text)::character varying, inspection.gid) AS id_sig
   FROM (((((itv."B01"
     JOIN itv.passage ON (("B01".passage_gid = passage.gid)))
     JOIN itv.inspection ON ((passage.inspection_gid = inspection.gid)))
     JOIN itv."B02" ON (("B02".passage_gid = passage.gid)))
     JOIN itv."B03" ON (("B03".passage_gid = passage.gid)))
     JOIN itv."B04" ON (("B04".passage_gid = passage.gid)))
  WHERE (("B01"."AAA" IS NOT NULL) AND (("B01"."AAA")::text <> ''::text))
  GROUP BY inspection.gid, "B01"."AAA", "B03"."ACA", "B03"."ACB", "B03"."ACC", "B03"."ACD", inspection.shp_coll_table;


ALTER VIEW itv.v_itv_physiq_coll OWNER TO postgres;

--
-- TOC entry 249 (class 1259 OID 23748)
-- Name: v_itv_physiq_reg; Type: VIEW; Schema: itv; Owner: postgres
--

CREATE VIEW itv.v_itv_physiq_reg AS
 WITH union_reg AS (
         SELECT inspection.gid AS inspection_gid,
            ("B01"."AAD")::text AS id_regard,
            NULLIF(("B03"."ACH")::text, 'NaN'::text) AS profondeur,
            NULL::character varying(1) AS forme
           FROM (((((itv."B01"
             JOIN itv."B02" ON (("B02".passage_gid = "B01".passage_gid)))
             JOIN itv."B03" ON (("B03".passage_gid = "B01".passage_gid)))
             JOIN itv."B04" ON (("B04".passage_gid = "B01".passage_gid)))
             JOIN itv.passage ON ((passage.gid = "B01".passage_gid)))
             JOIN itv.inspection ON ((inspection.gid = passage.inspection_gid)))
          WHERE (("B01"."AAD" IS NOT NULL) AND (("B01"."AAD")::text <> ''::text))
        UNION ALL
         SELECT inspection.gid AS gid_inspection,
            ("B01"."AAF")::text AS id_regard,
            NULLIF(("B03"."ACI")::text, 'NaN'::text) AS profondeur,
            NULL::character varying(1) AS forme
           FROM (((((itv."B01"
             JOIN itv."B02" ON (("B02".passage_gid = "B01".passage_gid)))
             JOIN itv."B03" ON (("B03".passage_gid = "B01".passage_gid)))
             JOIN itv."B04" ON (("B04".passage_gid = "B01".passage_gid)))
             JOIN itv.passage ON ((passage.gid = "B01".passage_gid)))
             JOIN itv.inspection ON ((inspection.gid = passage.inspection_gid)))
          WHERE (("B01"."AAF" IS NOT NULL) AND (("B01"."AAF")::text <> ''::text))
        )
 SELECT row_number() OVER () AS gid,
    inspection_gid,
    id_regard,
    COALESCE(max(NULLIF(profondeur, ''::text)), NULL::text) AS profondeur,
    NULL::text AS dimension,
    forme,
    itv.get_id_sig('ids_reg'::text, (id_regard)::character varying, inspection_gid) AS id_sig
   FROM union_reg
  GROUP BY inspection_gid, id_regard, forme, (itv.get_id_sig('ids_reg'::text, (id_regard)::character varying, inspection_gid));


ALTER VIEW itv.v_itv_physiq_reg OWNER TO postgres;

--
-- TOC entry 5685 (class 2604 OID 23753)
-- Name: B01 gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B01" ALTER COLUMN gid SET DEFAULT nextval('itv."B01_gid_seq"'::regclass);


--
-- TOC entry 5686 (class 2604 OID 23754)
-- Name: B02 gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B02" ALTER COLUMN gid SET DEFAULT nextval('itv."B02_gid_seq"'::regclass);


--
-- TOC entry 5687 (class 2604 OID 23755)
-- Name: B03 gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B03" ALTER COLUMN gid SET DEFAULT nextval('itv."B03_gid_seq"'::regclass);


--
-- TOC entry 5688 (class 2604 OID 23756)
-- Name: B04 gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B04" ALTER COLUMN gid SET DEFAULT nextval('itv."B04_gid_seq"'::regclass);


--
-- TOC entry 5689 (class 2604 OID 23757)
-- Name: C gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."C" ALTER COLUMN gid SET DEFAULT nextval('itv."C_gid_seq"'::regclass);


--
-- TOC entry 5690 (class 2604 OID 23758)
-- Name: commune gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.commune ALTER COLUMN gid SET DEFAULT nextval('itv.commune_gid_seq'::regclass);


--
-- TOC entry 5691 (class 2604 OID 23759)
-- Name: ids_coll gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.ids_coll ALTER COLUMN gid SET DEFAULT nextval('itv.correspondance_coll_gid_seq'::regclass);


--
-- TOC entry 5692 (class 2604 OID 23760)
-- Name: ids_reg gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.ids_reg ALTER COLUMN gid SET DEFAULT nextval('itv.correspondance_reg_gid_seq'::regclass);


--
-- TOC entry 5693 (class 2604 OID 23761)
-- Name: inspection gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.inspection ALTER COLUMN gid SET DEFAULT nextval('itv.inspection_gid_seq'::regclass);


--
-- TOC entry 5694 (class 2604 OID 23762)
-- Name: passage gid; Type: DEFAULT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.passage ALTER COLUMN gid SET DEFAULT nextval('itv.passage_gid_seq'::regclass);


--
-- TOC entry 5722 (class 2606 OID 25736)
-- Name: ids_reg PK_1a2b3c4d5e6f7g8h9i0j1k2l3m; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.ids_reg
    ADD CONSTRAINT "PK_1a2b3c4d5e6f7g8h9i0j1k2l3m" PRIMARY KEY (gid);


--
-- TOC entry 5710 (class 2606 OID 25738)
-- Name: C PK_4a936ec59e3abba7e9444c6cb4e; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."C"
    ADD CONSTRAINT "PK_4a936ec59e3abba7e9444c6cb4e" PRIMARY KEY (gid);


--
-- TOC entry 5717 (class 2606 OID 25740)
-- Name: ids_coll PK_4d5e6f7g8h9i0j1k2l3m4n5o6p; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.ids_coll
    ADD CONSTRAINT "PK_4d5e6f7g8h9i0j1k2l3m4n5o6p" PRIMARY KEY (gid);


--
-- TOC entry 5727 (class 2606 OID 25742)
-- Name: inspection PK_520b6d6420aa39867a4ef24e560; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.inspection
    ADD CONSTRAINT "PK_520b6d6420aa39867a4ef24e560" PRIMARY KEY (gid);


--
-- TOC entry 5707 (class 2606 OID 25744)
-- Name: B04 PK_605881ded05f29ee81b86547cc1; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B04"
    ADD CONSTRAINT "PK_605881ded05f29ee81b86547cc1" PRIMARY KEY (gid);


--
-- TOC entry 5702 (class 2606 OID 25746)
-- Name: B02 PK_9a7a5daac13f24b8e3efc42182c; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B02"
    ADD CONSTRAINT "PK_9a7a5daac13f24b8e3efc42182c" PRIMARY KEY (gid);


--
-- TOC entry 5729 (class 2606 OID 25748)
-- Name: passage PK_9f391f8e81e97c76afa2e044358; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.passage
    ADD CONSTRAINT "PK_9f391f8e81e97c76afa2e044358" PRIMARY KEY (gid);


--
-- TOC entry 5699 (class 2606 OID 25750)
-- Name: B01 PK_9f79f415c2fdf12ae8f44659e55; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B01"
    ADD CONSTRAINT "PK_9f79f415c2fdf12ae8f44659e55" PRIMARY KEY (gid);


--
-- TOC entry 5704 (class 2606 OID 25752)
-- Name: B03 PK_e2c43fe16299bd2e844615ca8ea; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B03"
    ADD CONSTRAINT "PK_e2c43fe16299bd2e844615ca8ea" PRIMARY KEY (gid);


--
-- TOC entry 5714 (class 2606 OID 25754)
-- Name: commune commune_pkey; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.commune
    ADD CONSTRAINT commune_pkey PRIMARY KEY (gid);


--
-- TOC entry 5719 (class 2606 OID 25756)
-- Name: ids_coll unique_coll_inspection_gid_id_itv; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.ids_coll
    ADD CONSTRAINT unique_coll_inspection_gid_id_itv UNIQUE (inspection_gid, id_itv);


--
-- TOC entry 5724 (class 2606 OID 25758)
-- Name: ids_reg unique_reg_inspection_gid_id_itv; Type: CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.ids_reg
    ADD CONSTRAINT unique_reg_inspection_gid_id_itv UNIQUE (inspection_gid, id_itv);


--
-- TOC entry 5695 (class 1259 OID 25759)
-- Name: IDX_1a2b3c4d5e6f7g8h9i0j1k2l3m; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "IDX_1a2b3c4d5e6f7g8h9i0j1k2l3m" ON itv."B01" USING btree ("AAD");


--
-- TOC entry 5700 (class 1259 OID 25760)
-- Name: IDX_3e4f5g6h7i8j9k0l1m2n3o4p5q; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "IDX_3e4f5g6h7i8j9k0l1m2n3o4p5q" ON itv."B02" USING btree (passage_gid);


--
-- TOC entry 5720 (class 1259 OID 25761)
-- Name: IDX_4e5f6g7h8i9j0k1l2m3n4o5p6q; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "IDX_4e5f6g7h8i9j0k1l2m3n4o5p6q" ON itv.ids_reg USING btree (inspection_gid);


--
-- TOC entry 5696 (class 1259 OID 25762)
-- Name: IDX_4n5o6p7q8r9s0t1u2v3w4x5y6z; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "IDX_4n5o6p7q8r9s0t1u2v3w4x5y6z" ON itv."B01" USING btree ("AAF");


--
-- TOC entry 5725 (class 1259 OID 25763)
-- Name: IDX_520b6d6420aa39867a4ef24e56; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "IDX_520b6d6420aa39867a4ef24e56" ON itv.inspection USING btree (gid);


--
-- TOC entry 5697 (class 1259 OID 25764)
-- Name: IDX_7a8b9c0d1e2f3g4h5i6j7k8l9m; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "IDX_7a8b9c0d1e2f3g4h5i6j7k8l9m" ON itv."B01" USING btree (passage_gid);


--
-- TOC entry 5715 (class 1259 OID 25765)
-- Name: IDX_9b8c7d6e5f4g3h2i1j0k1l2m3n; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "IDX_9b8c7d6e5f4g3h2i1j0k1l2m3n" ON itv.ids_coll USING btree (inspection_gid);


--
-- TOC entry 5712 (class 1259 OID 25766)
-- Name: commune_geom_geom_idx; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX commune_geom_geom_idx ON itv.commune USING gist (geom);


--
-- TOC entry 5730 (class 1259 OID 25767)
-- Name: idx_9f79f415c2fdf12ae8f44659e55; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX idx_9f79f415c2fdf12ae8f44659e55 ON itv.passage USING btree (inspection_gid);


--
-- TOC entry 5705 (class 1259 OID 25768)
-- Name: idx_B03_passage_gid; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "idx_B03_passage_gid" ON itv."B03" USING btree (passage_gid);


--
-- TOC entry 5708 (class 1259 OID 25769)
-- Name: idx_B04_passage_gid; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "idx_B04_passage_gid" ON itv."B04" USING btree (passage_gid);


--
-- TOC entry 5711 (class 1259 OID 25770)
-- Name: idx_C_passage_gid; Type: INDEX; Schema: itv; Owner: postgres
--

CREATE INDEX "idx_C_passage_gid" ON itv."C" USING btree (passage_gid);


--
-- TOC entry 5738 (class 2606 OID 25771)
-- Name: passage FK_1d981e67e559985e4245c91f03d; Type: FK CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.passage
    ADD CONSTRAINT "FK_1d981e67e559985e4245c91f03d" FOREIGN KEY (inspection_gid) REFERENCES itv.inspection(gid) ON DELETE CASCADE;


--
-- TOC entry 5731 (class 2606 OID 25776)
-- Name: B01 FK_20a4c933a0b94722664ee65b03f; Type: FK CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B01"
    ADD CONSTRAINT "FK_20a4c933a0b94722664ee65b03f" FOREIGN KEY (passage_gid) REFERENCES itv.passage(gid) ON DELETE CASCADE;


--
-- TOC entry 5735 (class 2606 OID 25781)
-- Name: C FK_20a4c933a0b94722664ee65b03f; Type: FK CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."C"
    ADD CONSTRAINT "FK_20a4c933a0b94722664ee65b03f" FOREIGN KEY (passage_gid) REFERENCES itv.passage(gid) ON DELETE CASCADE;


--
-- TOC entry 5732 (class 2606 OID 25786)
-- Name: B02 FK_2a3c15388b8af3f9d4f8ece1eb5; Type: FK CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B02"
    ADD CONSTRAINT "FK_2a3c15388b8af3f9d4f8ece1eb5" FOREIGN KEY (passage_gid) REFERENCES itv.passage(gid) ON DELETE CASCADE;


--
-- TOC entry 5737 (class 2606 OID 25791)
-- Name: ids_reg FK_3e4f5g6h7i8j9k0l1m2n3o4p5q; Type: FK CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.ids_reg
    ADD CONSTRAINT "FK_3e4f5g6h7i8j9k0l1m2n3o4p5q" FOREIGN KEY (inspection_gid) REFERENCES itv.inspection(gid) ON DELETE CASCADE;


--
-- TOC entry 5734 (class 2606 OID 25796)
-- Name: B04 FK_5646496fd947c2973f28ad5cd6f; Type: FK CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B04"
    ADD CONSTRAINT "FK_5646496fd947c2973f28ad5cd6f" FOREIGN KEY (passage_gid) REFERENCES itv.passage(gid) ON DELETE CASCADE;


--
-- TOC entry 5736 (class 2606 OID 25801)
-- Name: ids_coll FK_8a9b0c1d2e3f4g5h6i7j8k9l0m; Type: FK CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv.ids_coll
    ADD CONSTRAINT "FK_8a9b0c1d2e3f4g5h6i7j8k9l0m" FOREIGN KEY (inspection_gid) REFERENCES itv.inspection(gid) ON DELETE CASCADE;


--
-- TOC entry 5733 (class 2606 OID 25806)
-- Name: B03 FK_c616062b12032abe786ec91a1e1; Type: FK CONSTRAINT; Schema: itv; Owner: postgres
--

ALTER TABLE ONLY itv."B03"
    ADD CONSTRAINT "FK_c616062b12032abe786ec91a1e1" FOREIGN KEY (passage_gid) REFERENCES itv.passage(gid) ON DELETE CASCADE;


-- Completed on 2025-04-11 09:39:49

--
-- PostgreSQL database dump complete
--

