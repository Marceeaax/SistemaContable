-- Table: public.contacto

-- DROP TABLE IF EXISTS public.contacto;

CREATE TABLE IF NOT EXISTS public.contacto
(
    id_contacto integer NOT NULL DEFAULT nextval('contacto_id_contacto_seq'::regclass),
    id_cliente integer,
    nombre_contacto character varying(100) COLLATE pg_catalog."default",
    telefono character varying(50) COLLATE pg_catalog."default",
    email character varying(120) COLLATE pg_catalog."default",
    cargo character varying(100) COLLATE pg_catalog."default",
    CONSTRAINT contacto_pkey PRIMARY KEY (id_contacto)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.contacto
    OWNER to postgres;

-- Table: public.cuenta_contable

-- DROP TABLE IF EXISTS public.cuenta_contable;

CREATE TABLE IF NOT EXISTS public.cuenta_contable
(
    id_cuenta bigint NOT NULL DEFAULT nextval('cuenta_contable_id_cuenta_seq'::regclass),
    id_cliente integer NOT NULL,
    codigo character varying(20) COLLATE pg_catalog."default" NOT NULL,
    denominacion character varying(200) COLLATE pg_catalog."default" NOT NULL,
    alias character varying(50) COLLATE pg_catalog."default",
    categoria integer NOT NULL,
    imputable boolean NOT NULL,
    id_cuenta_madre bigint,
    cuenta_r173 character varying(20) COLLATE pg_catalog."default",
    denom_r173 character varying(200) COLLATE pg_catalog."default",
    en_uso boolean DEFAULT true,
    CONSTRAINT cuenta_contable_pkey PRIMARY KEY (id_cliente, id_cuenta),
    CONSTRAINT uq_cliente_codigo UNIQUE (id_cliente, codigo),
    CONSTRAINT fk_cuenta_madre FOREIGN KEY (id_cliente, id_cuenta_madre)
        REFERENCES public.cuenta_contable (id_cliente, id_cuenta) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.cuenta_contable
    OWNER to postgres;

-- Table: public.direccion

-- DROP TABLE IF EXISTS public.direccion;

CREATE TABLE IF NOT EXISTS public.direccion
(
    id_direccion integer NOT NULL DEFAULT nextval('direccion_id_direccion_seq'::regclass),
    id_cliente integer,
    tipo_direccion character varying(30) COLLATE pg_catalog."default" DEFAULT 'Fiscal'::character varying,
    direccion character varying(200) COLLATE pg_catalog."default",
    ciudad character varying(100) COLLATE pg_catalog."default",
    departamento character varying(100) COLLATE pg_catalog."default",
    CONSTRAINT direccion_pkey PRIMARY KEY (id_direccion)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.direccion
    OWNER to postgres;

-- Table: public.personas_ref

-- DROP TABLE IF EXISTS public.personas_ref;

CREATE TABLE IF NOT EXISTS public.personas_ref
(
    rf_tipo_ident character varying(3) COLLATE pg_catalog."default" NOT NULL,
    rf_numero character varying(15) COLLATE pg_catalog."default" NOT NULL,
    rf_pais_swift character(3) COLLATE pg_catalog."default" NOT NULL,
    rf_nombre character varying(60) COLLATE pg_catalog."default",
    rf_apellido character varying(60) COLLATE pg_catalog."default",
    rf_tipo_per smallint,
    rf_fecha_nac date,
    rf_ajuste_nac character(1) COLLATE pg_catalog."default",
    rf_version numeric(4,1) DEFAULT 1.0,
    rf_fecha_ver date DEFAULT CURRENT_DATE,
    rf_fecha_alta date DEFAULT CURRENT_DATE,
    rf_fecha_baja date,
    CONSTRAINT personas_ref_pk PRIMARY KEY (rf_tipo_ident, rf_numero, rf_pais_swift),
    CONSTRAINT personas_ref_ajuste_chk CHECK (rf_ajuste_nac = '*'::bpchar OR rf_ajuste_nac IS NULL)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.personas_ref
    OWNER to postgres;
-- Index: personas_ref_apellido_idx

-- DROP INDEX IF EXISTS public.personas_ref_apellido_idx;

CREATE INDEX IF NOT EXISTS personas_ref_apellido_idx
    ON public.personas_ref USING btree
    (rf_apellido COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: personas_ref_fecha_nac_idx

-- DROP INDEX IF EXISTS public.personas_ref_fecha_nac_idx;

CREATE INDEX IF NOT EXISTS personas_ref_fecha_nac_idx
    ON public.personas_ref USING btree
    (rf_fecha_nac ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: personas_ref_nombre_idx

-- DROP INDEX IF EXISTS public.personas_ref_nombre_idx;

CREATE INDEX IF NOT EXISTS personas_ref_nombre_idx
    ON public.personas_ref USING btree
    (rf_nombre COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: personas_ref_numero_idx

-- DROP INDEX IF EXISTS public.personas_ref_numero_idx;

CREATE INDEX IF NOT EXISTS personas_ref_numero_idx
    ON public.personas_ref USING btree
    (rf_numero COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;

-- Table: public.tipo_contribuyente

-- DROP TABLE IF EXISTS public.tipo_contribuyente;

CREATE TABLE IF NOT EXISTS public.tipo_contribuyente
(
    id_tipo integer NOT NULL DEFAULT nextval('tipo_contribuyente_id_tipo_seq'::regclass),
    nombre character varying(50) COLLATE pg_catalog."default" NOT NULL,
    descripcion text COLLATE pg_catalog."default",
    CONSTRAINT tipo_contribuyente_pkey PRIMARY KEY (id_tipo),
    CONSTRAINT tipo_contribuyente_nombre_key UNIQUE (nombre)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.tipo_contribuyente
    OWNER to postgres;

    -- Table: public.asiento

-- DROP TABLE IF EXISTS public.asiento;

CREATE TABLE IF NOT EXISTS public.asiento
(
    id_asiento bigint NOT NULL DEFAULT nextval('asiento_id_asiento_seq'::regclass),
    id_cliente integer NOT NULL,
    fecha date NOT NULL,
    descripcion character varying(300) COLLATE pg_catalog."default",
    referencia character varying(100) COLLATE pg_catalog."default",
    estado character varying(15) COLLATE pg_catalog."default" NOT NULL DEFAULT 'BORRADOR'::character varying,
    creado_en timestamp without time zone NOT NULL DEFAULT now(),
    CONSTRAINT asiento_pkey PRIMARY KEY (id_asiento),
    CONSTRAINT uq_asiento_cliente UNIQUE (id_asiento, id_cliente),
    CONSTRAINT asiento_id_cliente_fkey FOREIGN KEY (id_cliente)
        REFERENCES public.cliente (id_cliente) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT asiento_estado_check CHECK (estado::text = ANY (ARRAY['BORRADOR'::character varying, 'CONFIRMADO'::character varying, 'ANULADO'::character varying]::text[]))
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.asiento
    OWNER to postgres;

    -- Table: public.asiento_linea

-- DROP TABLE IF EXISTS public.asiento_linea;

CREATE TABLE IF NOT EXISTS public.asiento_linea
(
    id_linea bigint NOT NULL DEFAULT nextval('asiento_linea_id_linea_seq'::regclass),
    id_asiento bigint NOT NULL,
    id_cliente integer NOT NULL,
    id_cuenta bigint NOT NULL,
    glosa character varying(300) COLLATE pg_catalog."default",
    debe numeric(18,2) NOT NULL DEFAULT 0,
    haber numeric(18,2) NOT NULL DEFAULT 0,
    CONSTRAINT asiento_linea_pkey PRIMARY KEY (id_linea),
    CONSTRAINT fk_linea_asiento FOREIGN KEY (id_asiento, id_cliente)
        REFERENCES public.asiento (id_asiento, id_cliente) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_linea_cuenta FOREIGN KEY (id_cliente, id_cuenta)
        REFERENCES public.cuenta_contable (id_cliente, id_cuenta) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT chk_debe_haber CHECK (debe >= 0::numeric AND haber >= 0::numeric AND NOT (debe > 0::numeric AND haber > 0::numeric) AND NOT (debe = 0::numeric AND haber = 0::numeric))
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.asiento_linea
    OWNER to postgres;

    -- Table: public.cliente

-- DROP TABLE IF EXISTS public.cliente;

CREATE TABLE IF NOT EXISTS public.cliente
(
    id_cliente integer NOT NULL DEFAULT nextval('cliente_id_cliente_seq'::regclass),
    tipo_persona character(1) COLLATE pg_catalog."default" NOT NULL,
    nombre character varying(150) COLLATE pg_catalog."default" NOT NULL,
    ruc character varying(10) COLLATE pg_catalog."default" NOT NULL,
    dv character(1) COLLATE pg_catalog."default" NOT NULL,
    ci character varying(15) COLLATE pg_catalog."default",
    fecha_nacimiento date,
    fecha_constitucion date,
    direccion_principal character varying(200) COLLATE pg_catalog."default",
    telefono character varying(50) COLLATE pg_catalog."default",
    email character varying(120) COLLATE pg_catalog."default",
    correo_set character varying(120) COLLATE pg_catalog."default",
    contrasena_set character varying(120) COLLATE pg_catalog."default",
    vencimiento smallint,
    CONSTRAINT cliente_pkey PRIMARY KEY (id_cliente),
    CONSTRAINT unq_ruc UNIQUE (ruc, dv),
    CONSTRAINT cliente_tipo_persona_check CHECK (tipo_persona = ANY (ARRAY['F'::bpchar, 'J'::bpchar])),
    CONSTRAINT cliente_vencimiento_check CHECK (vencimiento >= 0 AND vencimiento <= 31)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.cliente
    OWNER to postgres;

-- Table: public.cliente_tipo_contribuyente

-- DROP TABLE IF EXISTS public.cliente_tipo_contribuyente;

CREATE TABLE IF NOT EXISTS public.cliente_tipo_contribuyente
(
    id_cliente_tipo integer NOT NULL DEFAULT nextval('cliente_tipo_contribuyente_id_cliente_tipo_seq'::regclass),
    id_cliente integer,
    id_tipo integer,
    fecha_alta date DEFAULT CURRENT_DATE,
    fecha_baja date,
    activo boolean DEFAULT true,
    CONSTRAINT cliente_tipo_contribuyente_pkey PRIMARY KEY (id_cliente_tipo),
    CONSTRAINT cliente_tipo_contribuyente_id_tipo_fkey FOREIGN KEY (id_tipo)
        REFERENCES public.tipo_contribuyente (id_tipo) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.cliente_tipo_contribuyente
    OWNER to postgres;



CREATE OR REPLACE FUNCTION public.calcular_dv_11_a(
    p_numero varchar,
    p_basemax integer DEFAULT 11
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_total integer := 0;
    v_resto integer;
    v_digit integer;
    v_numero_al text := '';
    v_caracter text;
    v_ascii integer;
    v_numero_aux integer;
    k integer := 2;
    i integer;
BEGIN
    IF p_numero IS NULL OR btrim(p_numero) = '' THEN
        RETURN NULL;
    END IF;

    -- Convierte letras a su código ASCII, números quedan igual
    FOR i IN 1 .. length(p_numero) LOOP
        v_caracter := upper(substr(p_numero, i, 1));
        v_ascii := ascii(v_caracter);

        IF v_ascii BETWEEN 48 AND 57 THEN
            v_numero_al := v_numero_al || v_caracter;
        ELSE
            v_numero_al := v_numero_al || v_ascii::text;
        END IF;
    END LOOP;

    -- Cálculo del DV
    k := 2;
    v_total := 0;

    FOR i IN REVERSE length(v_numero_al) .. 1 LOOP
        IF k > p_basemax THEN
            k := 2;
        END IF;

        v_numero_aux := substr(v_numero_al, i, 1)::integer;
        v_total := v_total + (v_numero_aux * k);
        k := k + 1;
    END LOOP;

    v_resto := mod(v_total, 11);

    IF v_resto > 1 THEN
        v_digit := 11 - v_resto;
    ELSE
        v_digit := 0;
    END IF;

    RETURN v_digit;
END;
$$;



SELECT public.calcular_dv_11_a('80082322'); 

select * from personas_ref where rf_numero = '1341595'

select * from personas_ref 

CREATE INDEX idx_personas_ref_numero_sin_guion
ON public.personas_ref ((REPLACE(rf_numero, '-', '')));

CREATE INDEX idx_personas_ref_numero_base
ON public.personas_ref ((split_part(rf_numero, '-', 1)));

select * from tipo_iva