-- public.audit_log definition

-- Drop table

-- DROP TABLE public.audit_log;

CREATE TABLE public.audit_log (
	id serial4 NOT NULL,
	usu_id int4 NULL,
	usuario varchar(80) DEFAULT 'anónimo'::character varying NOT NULL,
	accion varchar(20) NOT NULL,
	modulo varchar(50) NOT NULL,
	entidad_id int4 NULL,
	detalle text NULL,
	ip varchar(45) NULL,
	endpoint varchar(150) NULL,
	metodo varchar(10) NULL,
	status int2 DEFAULT 200 NULL,
	creado timestamptz DEFAULT now() NOT NULL,
	CONSTRAINT audit_log_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_audit_log_accion ON public.audit_log USING btree (accion);
CREATE INDEX ix_audit_log_creado ON public.audit_log USING btree (creado DESC);
CREATE INDEX ix_audit_log_modulo ON public.audit_log USING btree (modulo);
CREATE INDEX ix_audit_log_usu_id ON public.audit_log USING btree (usu_id);


-- public.audit_log foreign keys

ALTER TABLE public.audit_log ADD CONSTRAINT audit_log_usu_id_fkey FOREIGN KEY (usu_id) REFERENCES public.usuario(id) ON DELETE SET NULL;
