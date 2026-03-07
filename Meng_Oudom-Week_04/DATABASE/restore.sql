--
-- NOTE:
--
-- File paths need to be edited. Search for $$PATH$$ and
-- replace it with the path to the directory containing
-- the extracted data files.
--
--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4 (Debian 17.4-1.pgdg120+2)
-- Dumped by pg_dump version 17.4 (Debian 17.4-1.pgdg120+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE "de-week3";
--
-- Name: de-week3; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE "de-week3" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


ALTER DATABASE "de-week3" OWNER TO postgres;

\encoding SQL_ASCII
\connect -reuse-previous=on "dbname='de-week3'"

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: customers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customers (
    customer_id integer NOT NULL,
    full_name character varying(100),
    city character varying(50)
);


ALTER TABLE public.customers OWNER TO postgres;

--
-- Name: dim_customer; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dim_customer (
    customer_sk integer NOT NULL,
    customer_id integer,
    full_name character varying(100),
    city character varying(50)
);


ALTER TABLE public.dim_customer OWNER TO postgres;

--
-- Name: dim_date; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dim_date (
    date_sk integer NOT NULL,
    full_date date,
    year integer,
    month integer,
    day integer
);


ALTER TABLE public.dim_date OWNER TO postgres;

--
-- Name: dim_product; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dim_product (
    product_sk integer NOT NULL,
    product_id integer,
    product_name character varying(100),
    category character varying(50)
);


ALTER TABLE public.dim_product OWNER TO postgres;

--
-- Name: fact_sales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fact_sales (
    sales_id integer NOT NULL,
    date_sk integer,
    customer_sk integer,
    product_sk integer,
    store character varying(50),
    quantity integer,
    net_price numeric(10,2),
    discount numeric(10,2)
);


ALTER TABLE public.fact_sales OWNER TO postgres;

--
-- Name: fact_sales_sales_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fact_sales_sales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fact_sales_sales_id_seq OWNER TO postgres;

--
-- Name: fact_sales_sales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fact_sales_sales_id_seq OWNED BY public.fact_sales.sales_id;


--
-- Name: order_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.order_items (
    order_item_id integer NOT NULL,
    order_id integer,
    product_id integer,
    quantity integer,
    discount numeric(10,2)
);


ALTER TABLE public.order_items OWNER TO postgres;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.orders (
    order_id integer NOT NULL,
    customer_id integer,
    order_date date,
    store character varying(50)
);


ALTER TABLE public.orders OWNER TO postgres;

--
-- Name: products; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.products (
    product_id integer NOT NULL,
    product_name character varying(100),
    category character varying(50),
    price numeric(10,2)
);


ALTER TABLE public.products OWNER TO postgres;

--
-- Name: fact_sales sales_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_sales ALTER COLUMN sales_id SET DEFAULT nextval('public.fact_sales_sales_id_seq'::regclass);


--
-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.customers (customer_id, full_name, city) FROM stdin;
\.
COPY public.customers (customer_id, full_name, city) FROM '$$PATH$$/3403.dat';

--
-- Data for Name: dim_customer; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dim_customer (customer_sk, customer_id, full_name, city) FROM stdin;
\.
COPY public.dim_customer (customer_sk, customer_id, full_name, city) FROM '$$PATH$$/3407.dat';

--
-- Data for Name: dim_date; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dim_date (date_sk, full_date, year, month, day) FROM stdin;
\.
COPY public.dim_date (date_sk, full_date, year, month, day) FROM '$$PATH$$/3409.dat';

--
-- Data for Name: dim_product; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dim_product (product_sk, product_id, product_name, category) FROM stdin;
\.
COPY public.dim_product (product_sk, product_id, product_name, category) FROM '$$PATH$$/3408.dat';

--
-- Data for Name: fact_sales; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fact_sales (sales_id, date_sk, customer_sk, product_sk, store, quantity, net_price, discount) FROM stdin;
\.
COPY public.fact_sales (sales_id, date_sk, customer_sk, product_sk, store, quantity, net_price, discount) FROM '$$PATH$$/3411.dat';

--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.order_items (order_item_id, order_id, product_id, quantity, discount) FROM stdin;
\.
COPY public.order_items (order_item_id, order_id, product_id, quantity, discount) FROM '$$PATH$$/3406.dat';

--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.orders (order_id, customer_id, order_date, store) FROM stdin;
\.
COPY public.orders (order_id, customer_id, order_date, store) FROM '$$PATH$$/3405.dat';

--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.products (product_id, product_name, category, price) FROM stdin;
\.
COPY public.products (product_id, product_name, category, price) FROM '$$PATH$$/3404.dat';

--
-- Name: fact_sales_sales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fact_sales_sales_id_seq', 6, true);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);


--
-- Name: dim_customer dim_customer_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_customer
    ADD CONSTRAINT dim_customer_pkey PRIMARY KEY (customer_sk);


--
-- Name: dim_date dim_date_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_date
    ADD CONSTRAINT dim_date_pkey PRIMARY KEY (date_sk);


--
-- Name: dim_product dim_product_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dim_product
    ADD CONSTRAINT dim_product_pkey PRIMARY KEY (product_sk);


--
-- Name: fact_sales fact_sales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fact_sales
    ADD CONSTRAINT fact_sales_pkey PRIMARY KEY (sales_id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (order_item_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: orders orders_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- PostgreSQL database dump complete
--

