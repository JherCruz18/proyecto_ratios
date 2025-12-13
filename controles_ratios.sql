--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 16.4

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: insumos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.insumos (
    id_insumo integer NOT NULL,
    nombre character varying(255) NOT NULL,
    descripcion character varying(255),
    estado smallint DEFAULT 1,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.insumos OWNER TO postgres;

--
-- Name: insumos_id_insumo_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.insumos_id_insumo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.insumos_id_insumo_seq OWNER TO postgres;

--
-- Name: insumos_id_insumo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.insumos_id_insumo_seq OWNED BY public.insumos.id_insumo;


--
-- Name: registro_insumo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.registro_insumo (
    id_registro integer NOT NULL,
    id_insumo integer NOT NULL,
    id_sucursal integer NOT NULL,
    id_usuario integer NOT NULL,
    fecha date NOT NULL,
    stock_inicial integer NOT NULL,
    ingreso integer DEFAULT 0,
    consumo integer DEFAULT 0,
    reposicion integer DEFAULT 0,
    stock_final integer NOT NULL,
    venta_total numeric(12,2),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    ratio numeric
);


ALTER TABLE public.registro_insumo OWNER TO postgres;

--
-- Name: registro_insumo_id_registro_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.registro_insumo_id_registro_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.registro_insumo_id_registro_seq OWNER TO postgres;

--
-- Name: registro_insumo_id_registro_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.registro_insumo_id_registro_seq OWNED BY public.registro_insumo.id_registro;


--
-- Name: rol; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rol (
    id_rol integer NOT NULL,
    nombre character varying(255) NOT NULL,
    descripcion character varying(255),
    estado smallint DEFAULT 1
);


ALTER TABLE public.rol OWNER TO postgres;

--
-- Name: rol_id_rol_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rol_id_rol_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rol_id_rol_seq OWNER TO postgres;

--
-- Name: rol_id_rol_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rol_id_rol_seq OWNED BY public.rol.id_rol;


--
-- Name: sucursal; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sucursal (
    id_sucursal integer NOT NULL,
    nombre character varying(255) NOT NULL,
    estado smallint DEFAULT 1
);


ALTER TABLE public.sucursal OWNER TO postgres;

--
-- Name: sucursal_id_sucursal_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sucursal_id_sucursal_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sucursal_id_sucursal_seq OWNER TO postgres;

--
-- Name: sucursal_id_sucursal_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sucursal_id_sucursal_seq OWNED BY public.sucursal.id_sucursal;


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuario (
    id_usuario integer NOT NULL,
    nombre character varying(255) NOT NULL,
    apellido character varying(255) NOT NULL,
    correo character varying(255) NOT NULL,
    telefono character varying(20),
    id_rol integer NOT NULL,
    id_sucursal integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    username text,
    password character varying(255) DEFAULT '1234'::character varying NOT NULL
);


ALTER TABLE public.usuario OWNER TO postgres;

--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuario_id_usuario_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuario_id_usuario_seq OWNER TO postgres;

--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuario_id_usuario_seq OWNED BY public.usuario.id_usuario;


--
-- Name: v_ratio_insumo_carbon; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_ratio_insumo_carbon AS
 SELECT id_registro,
    id_insumo,
    id_sucursal,
    id_usuario,
    fecha,
    stock_inicial,
    consumo,
    round(
        CASE
            WHEN (stock_inicial > 0) THEN (((consumo)::numeric / (stock_inicial)::numeric) * (100)::numeric)
            ELSE (0)::numeric
        END, 2) AS ratio_porcentaje
   FROM public.registro_insumo;


ALTER VIEW public.v_ratio_insumo_carbon OWNER TO postgres;

--
-- Name: insumos id_insumo; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.insumos ALTER COLUMN id_insumo SET DEFAULT nextval('public.insumos_id_insumo_seq'::regclass);


--
-- Name: registro_insumo id_registro; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registro_insumo ALTER COLUMN id_registro SET DEFAULT nextval('public.registro_insumo_id_registro_seq'::regclass);


--
-- Name: rol id_rol; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol ALTER COLUMN id_rol SET DEFAULT nextval('public.rol_id_rol_seq'::regclass);


--
-- Name: sucursal id_sucursal; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sucursal ALTER COLUMN id_sucursal SET DEFAULT nextval('public.sucursal_id_sucursal_seq'::regclass);


--
-- Name: usuario id_usuario; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario ALTER COLUMN id_usuario SET DEFAULT nextval('public.usuario_id_usuario_seq'::regclass);


--
-- Data for Name: insumos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.insumos (id_insumo, nombre, descripcion, estado, created_at, updated_at) FROM stdin;
1	Carbón	\N	1	2025-12-09 19:10:38.961945	2025-12-09 19:10:38.961945
\.


--
-- Data for Name: registro_insumo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.registro_insumo (id_registro, id_insumo, id_sucursal, id_usuario, fecha, stock_inicial, ingreso, consumo, reposicion, stock_final, venta_total, created_at, updated_at, ratio) FROM stdin;
9	1	1	1	2025-12-10	63	135	90	0	108	21564.00	2025-12-11 00:12:50.312069	2025-12-11 00:12:50.312069	0.004173622704507512
10	1	1	2	2025-12-09	180	360	90	0	450	17961.00	2025-12-11 00:21:48.053975	2025-12-11 00:21:48.053975	0.005010856856522465
\.


--
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rol (id_rol, nombre, descripcion, estado) FROM stdin;
1	admin	\N	1
2	almacen	\N	1
3	gestor	\N	1
\.


--
-- Data for Name: sucursal; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sucursal (id_sucursal, nombre, estado) FROM stdin;
1	Cerro	1
2	Plaza	1
3	Larcomar	1
4	Prado	1
5	Remanso	1
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuario (id_usuario, nombre, apellido, correo, telefono, id_rol, id_sucursal, created_at, updated_at, username, password) FROM stdin;
1	admin	admin	admin@pardossurco.com	99999999	1	1	2025-12-09 16:52:06.417346	2025-12-09 16:52:06.417346	admin	1234
2	Pedro	Suarez	pedro@pardossurco.com	99999999	2	1	2025-12-11 00:20:16.759758	2025-12-11 00:20:16.759758	pedrosuarez	12345
\.


--
-- Name: insumos_id_insumo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.insumos_id_insumo_seq', 1, false);


--
-- Name: registro_insumo_id_registro_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.registro_insumo_id_registro_seq', 10, true);


--
-- Name: rol_id_rol_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rol_id_rol_seq', 3, true);


--
-- Name: sucursal_id_sucursal_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sucursal_id_sucursal_seq', 5, true);


--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuario_id_usuario_seq', 2, true);


--
-- Name: insumos insumos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.insumos
    ADD CONSTRAINT insumos_pkey PRIMARY KEY (id_insumo);


--
-- Name: registro_insumo registro_insumo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registro_insumo
    ADD CONSTRAINT registro_insumo_pkey PRIMARY KEY (id_registro);


--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id_rol);


--
-- Name: sucursal sucursal_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sucursal
    ADD CONSTRAINT sucursal_pkey PRIMARY KEY (id_sucursal);


--
-- Name: registro_insumo unq_registro_diario; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registro_insumo
    ADD CONSTRAINT unq_registro_diario UNIQUE (id_insumo, id_sucursal, fecha);


--
-- Name: usuario usuario_correo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_correo_key UNIQUE (correo);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id_usuario);


--
-- Name: unico_registro_diario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX unico_registro_diario ON public.registro_insumo USING btree (id_sucursal, id_insumo, fecha);


--
-- Name: registro_insumo fk_registro_insumo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registro_insumo
    ADD CONSTRAINT fk_registro_insumo FOREIGN KEY (id_insumo) REFERENCES public.insumos(id_insumo);


--
-- Name: registro_insumo fk_registro_sucursal; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registro_insumo
    ADD CONSTRAINT fk_registro_sucursal FOREIGN KEY (id_sucursal) REFERENCES public.sucursal(id_sucursal);


--
-- Name: registro_insumo fk_registro_usuario; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.registro_insumo
    ADD CONSTRAINT fk_registro_usuario FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario);


--
-- Name: usuario fk_usuario_rol; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol) REFERENCES public.rol(id_rol);


--
-- Name: usuario fk_usuario_sucursal; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT fk_usuario_sucursal FOREIGN KEY (id_sucursal) REFERENCES public.sucursal(id_sucursal);


--
-- PostgreSQL database dump complete
--

