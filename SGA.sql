BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "ARQUIVOS_anexo" (
	"id"	integer NOT NULL,
	"arquivo"	varchar(100) NOT NULL,
	"nome"	varchar(200) NOT NULL,
	"descricao"	text NOT NULL,
	"data_upload"	datetime NOT NULL,
	"documento_id"	bigint NOT NULL,
	"usuario_upload_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("documento_id") REFERENCES "ARQUIVOS_documento"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("usuario_upload_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_configuracaosistema" (
	"id"	integer NOT NULL,
	"chave"	varchar(100) NOT NULL UNIQUE,
	"valor"	text NOT NULL,
	"descricao"	text NOT NULL,
	"ativo"	bool NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_customuser" (
	"id"	integer NOT NULL,
	"password"	varchar(128) NOT NULL,
	"last_login"	datetime,
	"is_superuser"	bool NOT NULL,
	"username"	varchar(150) NOT NULL UNIQUE,
	"first_name"	varchar(150) NOT NULL,
	"last_name"	varchar(150) NOT NULL,
	"email"	varchar(254) NOT NULL,
	"is_staff"	bool NOT NULL,
	"is_active"	bool NOT NULL,
	"date_joined"	datetime NOT NULL,
	"nivel_acesso"	varchar(20) NOT NULL,
	"telefone"	varchar(15) NOT NULL,
	"created_at"	datetime NOT NULL,
	"departamento_id"	bigint,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("departamento_id") REFERENCES "ARQUIVOS_departamento"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_customuser_groups" (
	"id"	integer NOT NULL,
	"customuser_id"	bigint NOT NULL,
	"group_id"	integer NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("customuser_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("group_id") REFERENCES "auth_group"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_customuser_user_permissions" (
	"id"	integer NOT NULL,
	"customuser_id"	bigint NOT NULL,
	"permission_id"	integer NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("customuser_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("permission_id") REFERENCES "auth_permission"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_departamento" (
	"id"	integer NOT NULL,
	"nome"	varchar(255) NOT NULL,
	"codigo"	varchar(20) NOT NULL,
	"descricao"	text NOT NULL,
	"ativo"	bool NOT NULL,
	"created_at"	datetime NOT NULL,
	"responsavel_id"	bigint,
	"tipo_municipio"	varchar(1) NOT NULL,
	"tipo_departamento"	varchar(1) NOT NULL,
	"parent_id"	bigint,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("parent_id") REFERENCES "ARQUIVOS_departamento"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("responsavel_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_documento" (
	"id"	integer NOT NULL,
	"numero_protocolo"	varchar(20) NOT NULL UNIQUE,
	"titulo"	varchar(200) NOT NULL,
	"conteudo"	text NOT NULL,
	"arquivo"	varchar(100),
	"arquivo_digitalizado"	varchar(100),
	"status"	varchar(20) NOT NULL,
	"prioridade"	varchar(10) NOT NULL,
	"data_criacao"	datetime NOT NULL,
	"data_prazo"	datetime NOT NULL,
	"data_conclusao"	datetime,
	"tags"	varchar(500) NOT NULL,
	"observacoes"	text NOT NULL,
	"criado_por_id"	bigint NOT NULL,
	"departamento_atual_id"	bigint NOT NULL,
	"departamento_origem_id"	bigint NOT NULL,
	"responsavel_atual_id"	bigint,
	"tipo_documento_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("criado_por_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("departamento_atual_id") REFERENCES "ARQUIVOS_departamento"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("departamento_origem_id") REFERENCES "ARQUIVOS_departamento"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("responsavel_atual_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("tipo_documento_id") REFERENCES "ARQUIVOS_tipodocumento"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_movimentacaodocumento" (
	"id"	integer NOT NULL,
	"tipo_movimentacao"	varchar(20) NOT NULL,
	"data_movimentacao"	datetime NOT NULL,
	"observacoes"	text NOT NULL,
	"despacho"	text NOT NULL,
	"confirmado_recebimento"	bool NOT NULL,
	"data_confirmacao"	datetime,
	"departamento_destino_id"	bigint,
	"departamento_origem_id"	bigint,
	"documento_id"	bigint NOT NULL,
	"usuario_id"	bigint NOT NULL,
	"usuario_confirmacao_id"	bigint,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("departamento_destino_id") REFERENCES "ARQUIVOS_departamento"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("departamento_origem_id") REFERENCES "ARQUIVOS_departamento"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("documento_id") REFERENCES "ARQUIVOS_documento"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("usuario_confirmacao_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("usuario_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_notificacao" (
	"id"	integer NOT NULL,
	"mensagem"	varchar(255) NOT NULL,
	"link"	varchar(255),
	"data_criacao"	datetime NOT NULL,
	"lida"	bool NOT NULL,
	"usuario_id"	bigint NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("usuario_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "ARQUIVOS_tipodocumento" (
	"id"	integer NOT NULL,
	"nome"	varchar(50) NOT NULL UNIQUE,
	"descricao"	text NOT NULL,
	"prazo_dias"	integer NOT NULL,
	"ativo"	bool NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "auth_group" (
	"id"	integer NOT NULL,
	"name"	varchar(150) NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "auth_group_permissions" (
	"id"	integer NOT NULL,
	"group_id"	integer NOT NULL,
	"permission_id"	integer NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("group_id") REFERENCES "auth_group"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("permission_id") REFERENCES "auth_permission"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "auth_permission" (
	"id"	integer NOT NULL,
	"content_type_id"	integer NOT NULL,
	"codename"	varchar(100) NOT NULL,
	"name"	varchar(255) NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "django_admin_log" (
	"id"	integer NOT NULL,
	"object_id"	text,
	"object_repr"	varchar(200) NOT NULL,
	"action_flag"	smallint unsigned NOT NULL CHECK("action_flag" >= 0),
	"change_message"	text NOT NULL,
	"content_type_id"	integer,
	"user_id"	bigint NOT NULL,
	"action_time"	datetime NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id") DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY("user_id") REFERENCES "ARQUIVOS_customuser"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "django_content_type" (
	"id"	integer NOT NULL,
	"app_label"	varchar(100) NOT NULL,
	"model"	varchar(100) NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "ARQUIVOS_customuser" VALUES (1,'pbkdf2_sha256$600000$85CnKzGSrGfmv4LTDXlAzr$eiQ5JGQHG0WdjFCyzdE1YD8RX3XWxVMfs8Apu7b8H0s=','2025-09-07 14:48:17',1,'ruitunga','','','',1,1,'2025-05-28 20:23:06','diretor','','2025-05-28 20:23:06.814902',185);
INSERT INTO "ARQUIVOS_customuser" VALUES (2,'pbkdf2_sha256$870000$zClsPFIsB6JrChcoYtcl7u$xUViKQcMX4YGMOIlxyXMmcTiISLK8EfhmtyBNIXFZSs=','2025-08-26 20:34:49.664194',0,'Kajamba','','','',0,1,'2025-05-28 20:27:13','operador','','2025-05-28 20:27:14.110370',NULL);
INSERT INTO "ARQUIVOS_customuser" VALUES (3,'pbkdf2_sha256$600000$JhaAAPd3zNUm2NtAcxauHm$CMuoisAFjv06FJ0QGzdw9y37AUVafbxdKAEGHMEIKVg=','2025-09-07 12:28:52.059191',0,'Fernando','','','',0,1,'2025-05-28 20:28:04','operador','','2025-05-28 20:28:05.514410',186);
INSERT INTO "ARQUIVOS_customuser" VALUES (4,'pbkdf2_sha256$870000$mdMyU2kV0ZHLtD2zW0W4M3$tRRiS7P36OCsKK4hLeOWSh2oaqAoGMRAgdLvjKpy/Bw=','2025-05-29 09:37:11.436548',0,'Mauro','','','',0,1,'2025-05-28 20:28:46','operador','','2025-05-28 20:28:47.079677',NULL);
INSERT INTO "ARQUIVOS_customuser" VALUES (5,'pbkdf2_sha256$870000$OOI3fXEfsyT1FRvgUsvFPW$grO5qFSK5yag4diMUAAhCCVfvHSGL8pEuUe7BhwODwI=','2025-08-26 20:41:37',0,'FernandoMendes','','','',0,1,'2025-08-26 20:40:02','supervisor','','2025-08-26 20:40:05.389990',NULL);
INSERT INTO "ARQUIVOS_customuser" VALUES (6,'pbkdf2_sha256$600000$PNSD1DLpAAQDy6PaWNSmw3$qoeJTSq4OCbHA72hp5KT4yh+Uk+MeoQYLN6U8r2q3Aw=','2025-09-05 23:13:12',0,'Alegria','','','',0,1,'2025-08-26 20:41:24','operador','','2025-08-26 20:41:25.453100',187);
INSERT INTO "ARQUIVOS_customuser_groups" VALUES (1,3,1);
INSERT INTO "ARQUIVOS_customuser_groups" VALUES (2,6,1);
INSERT INTO "ARQUIVOS_customuser_user_permissions" VALUES (1,2,42);
INSERT INTO "ARQUIVOS_customuser_user_permissions" VALUES (2,3,42);
INSERT INTO "ARQUIVOS_customuser_user_permissions" VALUES (3,4,42);
INSERT INTO "ARQUIVOS_customuser_user_permissions" VALUES (4,6,42);
INSERT INTO "ARQUIVOS_departamento" VALUES (9,'Secretaria Geral','','',1,'2025-09-05 23:08:42.494837',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (10,'Secção de Orçamento, Finanças e Contratação Pública','','',1,'2025-09-05 23:08:42.516197',NULL,'A','A',9);
INSERT INTO "ARQUIVOS_departamento" VALUES (11,'Secção de Património, Logística e Protocolo','','',1,'2025-09-05 23:08:42.537368',NULL,'A','A',9);
INSERT INTO "ARQUIVOS_departamento" VALUES (12,'Secção de Expediente','','',1,'2025-09-05 23:08:42.558192',NULL,'A','A',9);
INSERT INTO "ARQUIVOS_departamento" VALUES (13,'Gabinete de Estudos, Planeamento e Estatística','','',1,'2025-09-05 23:08:42.583200',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (14,'Secção de Estudos e Estatística','','',1,'2025-09-05 23:08:42.606820',NULL,'A','A',13);
INSERT INTO "ARQUIVOS_departamento" VALUES (15,'Secção de Planeamento','','',1,'2025-09-05 23:08:42.639607',NULL,'A','A',13);
INSERT INTO "ARQUIVOS_departamento" VALUES (16,'Secção de Monitorização e Controlo','','',1,'2025-09-05 23:08:42.661354',NULL,'A','A',13);
INSERT INTO "ARQUIVOS_departamento" VALUES (17,'Gabinete de Recursos Humanos','','',1,'2025-09-05 23:08:42.683762',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (18,'Secção de Gestão Administrativa','','',1,'2025-09-05 23:08:42.706144',NULL,'A','A',17);
INSERT INTO "ARQUIVOS_departamento" VALUES (19,'Secção de Gestão de Carreiras e Capaitação Técnica','','',1,'2025-09-05 23:08:42.728882',NULL,'A','A',17);
INSERT INTO "ARQUIVOS_departamento" VALUES (20,'Gabinete de Comunicação Social','','',1,'2025-09-05 23:08:42.750160',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (21,'Secção de Comunicação Institucional e Imprensa','','',1,'2025-09-05 23:08:42.766704',NULL,'A','A',20);
INSERT INTO "ARQUIVOS_departamento" VALUES (22,'Secção para Documentação e Informação','','',1,'2025-09-05 23:08:42.778340',NULL,'A','A',20);
INSERT INTO "ARQUIVOS_departamento" VALUES (23,'Gabinete Jurídico e Apoio às Comissões de Moradores','','',1,'2025-09-05 23:08:42.792228',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (24,'Secção dos Assuntos Jurídicos, Contencioso e Intercâmbio','','',1,'2025-09-05 23:08:42.807904',NULL,'A','A',23);
INSERT INTO "ARQUIVOS_departamento" VALUES (25,'Secção de Acompanhamento e Apoio às Comissões de Moradores','','',1,'2025-09-05 23:08:42.821588',NULL,'A','A',23);
INSERT INTO "ARQUIVOS_departamento" VALUES (26,'Direcção Municipal da Educação','','',1,'2025-09-05 23:08:42.833892',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (27,'Secção de Educação e Ensino','','',1,'2025-09-05 23:08:42.846273',NULL,'A','A',26);
INSERT INTO "ARQUIVOS_departamento" VALUES (28,'Secção de Planeamento, Estatística e Recursos Humanos','','',1,'2025-09-05 23:08:42.855473',NULL,'A','A',26);
INSERT INTO "ARQUIVOS_departamento" VALUES (29,'Secção de Inspecção e Supervisão Pedagógica','','',1,'2025-09-05 23:08:42.864080',NULL,'A','A',26);
INSERT INTO "ARQUIVOS_departamento" VALUES (30,'Secção de Ciência, Tecnologia e Inovação','','',1,'2025-09-05 23:08:42.873575',NULL,'A','A',26);
INSERT INTO "ARQUIVOS_departamento" VALUES (31,'Direcção Municipal da Saúde','','',1,'2025-09-05 23:08:42.882084',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (32,'Secção de Logística Hospitalar e Depósito de Medicamentos','','',1,'2025-09-05 23:08:42.890445',NULL,'A','A',31);
INSERT INTO "ARQUIVOS_departamento" VALUES (33,'Secção de Estatística, Planeamento e Recursos Humanos','','',1,'2025-09-05 23:08:42.904135',NULL,'A','A',31);
INSERT INTO "ARQUIVOS_departamento" VALUES (34,'Secção de Saúde Pública','','',1,'2025-09-05 23:08:42.918383',NULL,'A','A',31);
INSERT INTO "ARQUIVOS_departamento" VALUES (35,'Secção de Inspecção de Saúde','','',1,'2025-09-05 23:08:42.931970',NULL,'A','A',31);
INSERT INTO "ARQUIVOS_departamento" VALUES (36,'Direcção Municipal de Promoção do Desenvolvimento Económico Integrado','','',1,'2025-09-05 23:08:42.945569',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (37,'Secção de Promoção do Desenvolvimento Económico Integrado','','',1,'2025-09-05 23:08:42.966302',NULL,'A','A',36);
INSERT INTO "ARQUIVOS_departamento" VALUES (38,'Secção de Licenciamento das Actividades Económicas e Serviços','','',1,'2025-09-05 23:08:42.987810',NULL,'A','A',36);
INSERT INTO "ARQUIVOS_departamento" VALUES (39,'Direção Municipal da Fiscalização e Inspecção das Actividades Económicas e Segurança Alimentar','','',1,'2025-09-05 23:08:43.008317',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (40,'Secção Municipal de Fiscalização','','',1,'2025-09-05 23:08:43.028915',NULL,'A','A',39);
INSERT INTO "ARQUIVOS_departamento" VALUES (41,'Secção Municipal de Inspecção das Actividades Económicas e Segurança Alimentar','','',1,'2025-09-05 23:08:43.058914',NULL,'A','A',39);
INSERT INTO "ARQUIVOS_departamento" VALUES (42,'Direcção Municipal do Turismo e Cultura','','',1,'2025-09-05 23:08:43.089984',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (43,'Secção do Turismo','','',1,'2025-09-05 23:08:43.121924',NULL,'A','A',42);
INSERT INTO "ARQUIVOS_departamento" VALUES (44,'Secção de Promoção da cultura','','',1,'2025-09-05 23:08:43.158608',NULL,'A','A',42);
INSERT INTO "ARQUIVOS_departamento" VALUES (45,'Direcção Municipal de Tempos Livres, Juventude e Desportos','','',1,'2025-09-05 23:08:43.185658',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (46,'Secção de Tempos Livres','','',1,'2025-09-05 23:08:43.210063',NULL,'A','A',45);
INSERT INTO "ARQUIVOS_departamento" VALUES (47,'Secção de Juventude e Desportos','','',1,'2025-09-05 23:08:43.232989',NULL,'A','A',45);
INSERT INTO "ARQUIVOS_departamento" VALUES (48,'Direcção Municipal da Acção Social, Família e Igualdade de Género','','',1,'2025-09-05 23:08:43.253435',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (49,'Secção de Acção Social','','',1,'2025-09-05 23:08:43.272315',NULL,'A','A',48);
INSERT INTO "ARQUIVOS_departamento" VALUES (50,'Secção de Família e Igualdade do Género','','',1,'2025-09-05 23:08:43.291784',NULL,'A','A',48);
INSERT INTO "ARQUIVOS_departamento" VALUES (51,'Direcção Municipal de Infra-estruturas, Ordenamento do Território e Habitação','','',1,'2025-09-05 23:08:43.310645',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (52,'Secção do Ordenamento do Território','','',1,'2025-09-05 23:08:43.331628',NULL,'A','A',51);
INSERT INTO "ARQUIVOS_departamento" VALUES (53,'Secção de Habitação','','',1,'2025-09-05 23:08:43.356076',NULL,'A','A',51);
INSERT INTO "ARQUIVOS_departamento" VALUES (54,'Secção de Infra-estruturas','','',1,'2025-09-05 23:08:43.371145',NULL,'A','A',51);
INSERT INTO "ARQUIVOS_departamento" VALUES (55,'Direcção Municipal do Ambiente e Saneamento Básico','','',1,'2025-09-05 23:08:43.385792',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (56,'Secção do Ambiente','','',1,'2025-09-05 23:08:43.403686',NULL,'A','A',55);
INSERT INTO "ARQUIVOS_departamento" VALUES (57,'Secção do Saneamento Básico','','',1,'2025-09-05 23:08:43.414979',NULL,'A','A',55);
INSERT INTO "ARQUIVOS_departamento" VALUES (58,'Direcção Municipal de Transportes, Tráfego e Mobilidade','','',1,'2025-09-05 23:08:43.425816',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (59,'Secção de Transportes','','',1,'2025-09-05 23:08:43.439297',NULL,'A','A',58);
INSERT INTO "ARQUIVOS_departamento" VALUES (60,'Secção de Tráfego e Mobilidade','','',1,'2025-09-05 23:08:43.452461',NULL,'A','A',58);
INSERT INTO "ARQUIVOS_departamento" VALUES (61,'Direcção Municipal de Energias e Águas','','',1,'2025-09-05 23:08:43.466366',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (62,'Secção de Serviços Municipalizados de Energia','','',1,'2025-09-05 23:08:43.482131',NULL,'A','A',61);
INSERT INTO "ARQUIVOS_departamento" VALUES (63,'Secção de Serviços Municipalizados das Água','','',1,'2025-09-05 23:08:43.496852',NULL,'A','A',61);
INSERT INTO "ARQUIVOS_departamento" VALUES (64,'Direcção Municipal de Agricultura, Pecuária e Pescas','','',1,'2025-09-05 23:08:43.511506',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (65,'Secção de Agricultura','','',1,'2025-09-05 23:08:43.528118',NULL,'A','A',64);
INSERT INTO "ARQUIVOS_departamento" VALUES (66,'Secção de Pecuária e Pescas','','',1,'2025-09-05 23:08:43.545417',NULL,'A','A',64);
INSERT INTO "ARQUIVOS_departamento" VALUES (67,'Direcção Municipal dos Registos e Modernização Administrativa','','',1,'2025-09-05 23:08:43.560126',NULL,'A','A',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (68,'Secção de Administração Pública e Trabalho','','',1,'2025-09-05 23:08:43.571335',NULL,'A','A',67);
INSERT INTO "ARQUIVOS_departamento" VALUES (69,'Secção de Registo Eleitoral, Recenseamento Militar e Organização do Território','','',1,'2025-09-05 23:08:43.587386',NULL,'A','A',67);
INSERT INTO "ARQUIVOS_departamento" VALUES (70,'Secção de Modernização Administrativa, e Gestão do Balcão Único de Atendimento ao Público (BUAP)','','',1,'2025-09-05 23:08:43.601545',NULL,'A','A',67);
INSERT INTO "ARQUIVOS_departamento" VALUES (71,'Secretaria Geral','','',1,'2025-09-05 23:08:43.615407',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (72,'Secção de Orçamento, Finanças e Contratação Pública','','',1,'2025-09-05 23:08:43.642376',NULL,'B','B',71);
INSERT INTO "ARQUIVOS_departamento" VALUES (73,'Secção de Património, Logística e Protocolo','','',1,'2025-09-05 23:08:43.670667',NULL,'B','B',71);
INSERT INTO "ARQUIVOS_departamento" VALUES (74,'Secção de Expediente','','',1,'2025-09-05 23:08:43.690746',NULL,'B','B',71);
INSERT INTO "ARQUIVOS_departamento" VALUES (75,'Gabinete de Estudos, Planeamento e Estatística','','',1,'2025-09-05 23:08:43.708196',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (76,'Secção de Estudos e Estatística','','',1,'2025-09-05 23:08:43.724744',NULL,'B','B',75);
INSERT INTO "ARQUIVOS_departamento" VALUES (77,'Secção de Planeamento','','',1,'2025-09-05 23:08:43.737916',NULL,'B','B',75);
INSERT INTO "ARQUIVOS_departamento" VALUES (78,'Secção de Monitorização e Controlo','','',1,'2025-09-05 23:08:43.756077',NULL,'B','B',75);
INSERT INTO "ARQUIVOS_departamento" VALUES (79,'Gabinete de Recursos Humanos','','',1,'2025-09-05 23:08:43.773654',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (80,'Secção de Gestão Administrativa','','',1,'2025-09-05 23:08:43.791443',NULL,'B','B',79);
INSERT INTO "ARQUIVOS_departamento" VALUES (81,'Secção de Gestão de Carreiras e Capaitação Técnica','','',1,'2025-09-05 23:08:43.808659',NULL,'B','B',79);
INSERT INTO "ARQUIVOS_departamento" VALUES (82,'Gabinete de Comunicação Social','','',1,'2025-09-05 23:08:43.827626',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (83,'Secção de Comunicação Institucional e Imprensa','','',1,'2025-09-05 23:08:43.846729',NULL,'B','B',82);
INSERT INTO "ARQUIVOS_departamento" VALUES (84,'Secção para Documentação e Informação','','',1,'2025-09-05 23:08:43.863847',NULL,'B','B',82);
INSERT INTO "ARQUIVOS_departamento" VALUES (85,'Gabinete Jurídico e Apoio às Comissões de Moradores','','',1,'2025-09-05 23:08:43.876809',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (86,'Secção dos Assuntos Jurídicos, Contencioso e Intercâmbio','','',1,'2025-09-05 23:08:43.888907',NULL,'B','B',85);
INSERT INTO "ARQUIVOS_departamento" VALUES (87,'Secção de Acompanhamento e Apoio às Comissões de Moradores','','',1,'2025-09-05 23:08:43.897786',NULL,'B','B',85);
INSERT INTO "ARQUIVOS_departamento" VALUES (88,'Direcção Municipal da Educação','','',1,'2025-09-05 23:08:43.906761',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (89,'Secção de Educação e Ensino','','',1,'2025-09-05 23:08:43.915205',NULL,'B','B',88);
INSERT INTO "ARQUIVOS_departamento" VALUES (90,'Secção de Planeamento, Estatística e Recursos Humanos','','',1,'2025-09-05 23:08:43.924339',NULL,'B','B',88);
INSERT INTO "ARQUIVOS_departamento" VALUES (91,'Secção de Inspecção e Supervisão Pedagógica','','',1,'2025-09-05 23:08:43.934168',NULL,'B','B',88);
INSERT INTO "ARQUIVOS_departamento" VALUES (92,'Secção de Ciência, Tecnologia e Inovação','','',1,'2025-09-05 23:08:43.952926',NULL,'B','B',88);
INSERT INTO "ARQUIVOS_departamento" VALUES (93,'Direcção Municipal da Saúde','','',1,'2025-09-05 23:08:43.968478',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (94,'Secção de Logística Hospitalar e Depósito de Medicamentos','','',1,'2025-09-05 23:08:43.984327',NULL,'B','B',93);
INSERT INTO "ARQUIVOS_departamento" VALUES (95,'Secção de Estatística, Planeamento e Recursos Humanos','','',1,'2025-09-05 23:08:43.999002',NULL,'B','B',93);
INSERT INTO "ARQUIVOS_departamento" VALUES (96,'Secção de Saúde Pública','','',1,'2025-09-05 23:08:44.010234',NULL,'B','B',93);
INSERT INTO "ARQUIVOS_departamento" VALUES (97,'Secção de Inspecção de Saúde','','',1,'2025-09-05 23:08:44.018282',NULL,'B','B',93);
INSERT INTO "ARQUIVOS_departamento" VALUES (98,'Direcção Municipal de Promoção do Desenvolvimento Económico Integrado','','',1,'2025-09-05 23:08:44.028627',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (99,'Secção de Promoção do Desenvolvimento Económico Integrado','','',1,'2025-09-05 23:08:44.041183',NULL,'B','B',98);
INSERT INTO "ARQUIVOS_departamento" VALUES (100,'Secção de Licenciamento das Actividades Económicas e Serviços','','',1,'2025-09-05 23:08:44.055809',NULL,'B','B',98);
INSERT INTO "ARQUIVOS_departamento" VALUES (101,'Direção Municipal da Fiscalização e Inspecção das Actividades Económicas e Segurança Alimentar','','',1,'2025-09-05 23:08:44.083215',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (102,'Secção Municipal de Fiscalização','','',1,'2025-09-05 23:08:44.102386',NULL,'B','B',101);
INSERT INTO "ARQUIVOS_departamento" VALUES (103,'Secção Municipal de Inspecção das Actividades Económicas e Segurança Alimentar','','',1,'2025-09-05 23:08:44.121458',NULL,'B','B',101);
INSERT INTO "ARQUIVOS_departamento" VALUES (104,'Direcção Municipal do Turismo, Cultura, Tempos Livres, Juventude e Desportos','','',1,'2025-09-05 23:08:44.139367',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (105,'Secção do Turismo','','',1,'2025-09-05 23:08:44.157713',NULL,'B','B',104);
INSERT INTO "ARQUIVOS_departamento" VALUES (106,'Secção de Promoção da cultura','','',1,'2025-09-05 23:08:44.172130',NULL,'B','B',104);
INSERT INTO "ARQUIVOS_departamento" VALUES (107,'Secção de Tempos Livres, Juventude e Desportos','','',1,'2025-09-05 23:08:44.185455',NULL,'B','B',104);
INSERT INTO "ARQUIVOS_departamento" VALUES (108,'Direcção Municipal da Acção Social, Família e Igualdade de Género','','',1,'2025-09-05 23:08:44.198458',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (109,'Secção de Acção Social','','',1,'2025-09-05 23:08:44.210492',NULL,'B','B',108);
INSERT INTO "ARQUIVOS_departamento" VALUES (110,'Secção de Família e Igualdade do Género','','',1,'2025-09-05 23:08:44.222896',NULL,'B','B',108);
INSERT INTO "ARQUIVOS_departamento" VALUES (111,'Direcção Municipal de Infra-estruturas, Ordenamento do Território e Habitação','','',1,'2025-09-05 23:08:44.240503',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (112,'Secção do Ordenamento do Território','','',1,'2025-09-05 23:08:44.258122',NULL,'B','B',111);
INSERT INTO "ARQUIVOS_departamento" VALUES (113,'Secção de Habitação','','',1,'2025-09-05 23:08:44.275900',NULL,'B','B',111);
INSERT INTO "ARQUIVOS_departamento" VALUES (114,'Secção de Infra-estruturas','','',1,'2025-09-05 23:08:44.297117',NULL,'B','B',111);
INSERT INTO "ARQUIVOS_departamento" VALUES (115,'Direcção Municipal do Ambiente e Saneamento Básico','','',1,'2025-09-05 23:08:44.310407',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (116,'Secção do Ambiente','','',1,'2025-09-05 23:08:44.321492',NULL,'B','B',115);
INSERT INTO "ARQUIVOS_departamento" VALUES (117,'Secção do Saneamento Básico','','',1,'2025-09-05 23:08:44.330239',NULL,'B','B',115);
INSERT INTO "ARQUIVOS_departamento" VALUES (118,'Direcção Municipal de Transportes, Tráfego e Mobilidade','','',1,'2025-09-05 23:08:44.338910',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (119,'Secção de Transportes','','',1,'2025-09-05 23:08:44.348173',NULL,'B','B',118);
INSERT INTO "ARQUIVOS_departamento" VALUES (120,'Secção de Tráfego e Mobilidade','','',1,'2025-09-05 23:08:44.358444',NULL,'B','B',118);
INSERT INTO "ARQUIVOS_departamento" VALUES (121,'Direcção Municipal de Energias e Águas','','',1,'2025-09-05 23:08:44.372037',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (122,'Secção de Serviços Municipalizados de Energia','','',1,'2025-09-05 23:08:44.385476',NULL,'B','B',121);
INSERT INTO "ARQUIVOS_departamento" VALUES (123,'Secção de Serviços Municipalizados das Água','','',1,'2025-09-05 23:08:44.399224',NULL,'B','B',121);
INSERT INTO "ARQUIVOS_departamento" VALUES (124,'Direcção Municipal de Agricultura, Pecuária e Pescas','','',1,'2025-09-05 23:08:44.411428',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (125,'Secção de Agricultura','','',1,'2025-09-05 23:08:44.421312',NULL,'B','B',124);
INSERT INTO "ARQUIVOS_departamento" VALUES (126,'Secção de Pecuária e Pescas','','',1,'2025-09-05 23:08:44.430520',NULL,'B','B',124);
INSERT INTO "ARQUIVOS_departamento" VALUES (127,'Direcção Municipal dos Registos e Modernização Administrativa','','',1,'2025-09-05 23:08:44.439287',NULL,'B','B',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (128,'Secção de Administração Pública e Trabalho','','',1,'2025-09-05 23:08:44.447918',NULL,'B','B',127);
INSERT INTO "ARQUIVOS_departamento" VALUES (129,'Secção de Registo Eleitoral, Recenseamento Militar e Organização do Território','','',1,'2025-09-05 23:08:44.458975',NULL,'B','B',127);
INSERT INTO "ARQUIVOS_departamento" VALUES (130,'Secção de Modernização Administrativa, e Gestão do Balcão Único de Atendimento ao Público (BUAP)','','',1,'2025-09-05 23:08:44.476336',NULL,'B','B',127);
INSERT INTO "ARQUIVOS_departamento" VALUES (131,'Secretaria Geral','','',1,'2025-09-05 23:08:44.503187',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (132,'Secção de Orçamento, Finanças e Contratação Pública','','',1,'2025-09-05 23:08:44.529475',NULL,'C','C',131);
INSERT INTO "ARQUIVOS_departamento" VALUES (133,'Secção de Património, Logística e Protocolo','','',1,'2025-09-05 23:08:44.553603',NULL,'C','C',131);
INSERT INTO "ARQUIVOS_departamento" VALUES (134,'Secção de Expediente','','',1,'2025-09-05 23:08:44.572280',NULL,'C','C',131);
INSERT INTO "ARQUIVOS_departamento" VALUES (135,'Gabinete de Estudos, Planeamento e Estatística','','',1,'2025-09-05 23:08:44.588178',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (136,'Secção de Estudos e Estatística','','',1,'2025-09-05 23:08:44.601567',NULL,'C','C',135);
INSERT INTO "ARQUIVOS_departamento" VALUES (137,'Secção de Planeamento','','',1,'2025-09-05 23:08:44.615591',NULL,'C','C',135);
INSERT INTO "ARQUIVOS_departamento" VALUES (138,'Secção de Monitorização e Controlo','','',1,'2025-09-05 23:08:44.628870',NULL,'C','C',135);
INSERT INTO "ARQUIVOS_departamento" VALUES (139,'Gabinete de Recursos Humanos','','',1,'2025-09-05 23:08:44.641318',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (140,'Secção de Gestão Administrativa','','',1,'2025-09-05 23:08:44.659008',NULL,'C','C',139);
INSERT INTO "ARQUIVOS_departamento" VALUES (141,'Secção de Gestão de Carreiras e Capaitação Técnica','','',1,'2025-09-05 23:08:44.677833',NULL,'C','C',139);
INSERT INTO "ARQUIVOS_departamento" VALUES (142,'Gabinete de Comunicação Social','','',1,'2025-09-05 23:08:44.694755',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (143,'Secção de Comunicação Institucional e Imprensa','','',1,'2025-09-05 23:08:44.716056',NULL,'C','C',142);
INSERT INTO "ARQUIVOS_departamento" VALUES (144,'Secção para Documentação e Informação','','',1,'2025-09-05 23:08:44.738134',NULL,'C','C',142);
INSERT INTO "ARQUIVOS_departamento" VALUES (145,'Gabinete Jurídico e Apoio às Comissões de Moradores','','',1,'2025-09-05 23:08:44.756304',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (146,'Secção dos Assuntos Jurídicos, Contencioso e Intercâmbio','','',1,'2025-09-05 23:08:44.769599',NULL,'C','C',145);
INSERT INTO "ARQUIVOS_departamento" VALUES (147,'Secção de Acompanhamento e Apoio às Comissões de Moradores','','',1,'2025-09-05 23:08:44.779963',NULL,'C','C',145);
INSERT INTO "ARQUIVOS_departamento" VALUES (148,'Direcção Municipal da Educação','','',1,'2025-09-05 23:08:44.790444',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (149,'Secção de Educação e Ensino','','',1,'2025-09-05 23:08:44.801131',NULL,'C','C',148);
INSERT INTO "ARQUIVOS_departamento" VALUES (150,'Secção de Planeamento, Estatística e Recursos Humanos','','',1,'2025-09-05 23:08:44.818049',NULL,'C','C',148);
INSERT INTO "ARQUIVOS_departamento" VALUES (151,'Secção de Inspecção e Supervisão Pedagógica','','',1,'2025-09-05 23:08:44.832242',NULL,'C','C',148);
INSERT INTO "ARQUIVOS_departamento" VALUES (152,'Secção de Ciência, Tecnologia e Inovação','','',1,'2025-09-05 23:08:44.845360',NULL,'C','C',148);
INSERT INTO "ARQUIVOS_departamento" VALUES (153,'Direcção Municipal da Saúde','','',1,'2025-09-05 23:08:44.857708',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (154,'Secção de Logística Hospitalar e Depósito de Medicamentos','','',1,'2025-09-05 23:08:44.871935',NULL,'C','C',153);
INSERT INTO "ARQUIVOS_departamento" VALUES (155,'Secção de Estatística, Planeamento e Recursos Humanos','','',1,'2025-09-05 23:08:44.881246',NULL,'C','C',153);
INSERT INTO "ARQUIVOS_departamento" VALUES (156,'Secção de Saúde Pública','','',1,'2025-09-05 23:08:44.890040',NULL,'C','C',153);
INSERT INTO "ARQUIVOS_departamento" VALUES (157,'Secção de Inspecção de Saúde','','',1,'2025-09-05 23:08:44.899438',NULL,'C','C',153);
INSERT INTO "ARQUIVOS_departamento" VALUES (158,'Direcção Municipal de Promoção do Desenvolvimento Económico Integrado','','',1,'2025-09-05 23:08:44.908253',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (159,'Secção de Promoção do Desenvolvimento Económico Integrado','','',1,'2025-09-05 23:08:44.924448',NULL,'C','C',158);
INSERT INTO "ARQUIVOS_departamento" VALUES (160,'Secção de Licenciamento das Actividades Económicas e Serviços','','',1,'2025-09-05 23:08:44.938865',NULL,'C','C',158);
INSERT INTO "ARQUIVOS_departamento" VALUES (161,'Direção Municipal da Fiscalização e Inspecção das Actividades Económicas e Segurança Alimentar','','',1,'2025-09-05 23:08:44.956466',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (162,'Secção Municipal de Fiscalização','','',1,'2025-09-05 23:08:44.974281',NULL,'C','C',161);
INSERT INTO "ARQUIVOS_departamento" VALUES (163,'Secção Municipal de Inspecção das Actividades Económicas e Segurança Alimentar','','',1,'2025-09-05 23:08:44.993098',NULL,'C','C',161);
INSERT INTO "ARQUIVOS_departamento" VALUES (164,'Direcção Municipal da Acção Social, Turismo, Cultura, Juventude e Desportos','','',1,'2025-09-05 23:08:45.008220',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (165,'Secção de Promoção do Turismo e cultura','','',1,'2025-09-05 23:08:45.024813',NULL,'C','C',164);
INSERT INTO "ARQUIVOS_departamento" VALUES (166,'Secção de Juventude e Desportos','','',1,'2025-09-05 23:08:45.038974',NULL,'C','C',164);
INSERT INTO "ARQUIVOS_departamento" VALUES (167,'Secção da Secção de Acção Social','','',1,'2025-09-05 23:08:45.052615',NULL,'C','C',164);
INSERT INTO "ARQUIVOS_departamento" VALUES (168,'Direcção Municipal de Infra-estruturas, Ordenamento do Território, Habitação, Ambiente e Saneamento Básico','','',1,'2025-09-05 23:08:45.068546',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (169,'Secção do Ordenamento do Território e Habitação','','',1,'2025-09-05 23:08:45.086937',NULL,'C','C',168);
INSERT INTO "ARQUIVOS_departamento" VALUES (170,'Secção de Infra-estruturas','','',1,'2025-09-05 23:08:45.104949',NULL,'C','C',168);
INSERT INTO "ARQUIVOS_departamento" VALUES (171,'Secção do Ambiente e Saneamento Básico','','',1,'2025-09-05 23:08:45.122245',NULL,'C','C',168);
INSERT INTO "ARQUIVOS_departamento" VALUES (172,'Direcção Municipal de Transportes, Tráfego e Mobilidade','','',1,'2025-09-05 23:08:45.146180',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (173,'Secção de Transportes','','',1,'2025-09-05 23:08:45.162836',NULL,'C','C',172);
INSERT INTO "ARQUIVOS_departamento" VALUES (174,'Secção de Tráfego e Mobilidade','','',1,'2025-09-05 23:08:45.174813',NULL,'C','C',172);
INSERT INTO "ARQUIVOS_departamento" VALUES (175,'Direcção Municipal de Energias e Águas','','',1,'2025-09-05 23:08:45.187308',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (176,'Secção de Serviços Municipalizados de Energia','','',1,'2025-09-05 23:08:45.199789',NULL,'C','C',175);
INSERT INTO "ARQUIVOS_departamento" VALUES (177,'Secção de Serviços Municipalizados das Água','','',1,'2025-09-05 23:08:45.211063',NULL,'C','C',175);
INSERT INTO "ARQUIVOS_departamento" VALUES (178,'Direcção Municipal de Agricultura, Pecuária e Pescas','','',1,'2025-09-05 23:08:45.224316',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (179,'Secção de Agricultura','','',1,'2025-09-05 23:08:45.242515',NULL,'C','C',178);
INSERT INTO "ARQUIVOS_departamento" VALUES (180,'Secção de Pecuária e Pescas','','',1,'2025-09-05 23:08:45.258486',NULL,'C','C',178);
INSERT INTO "ARQUIVOS_departamento" VALUES (181,'Direcção Municipal dos Registos e Modernização Administrativa','','',1,'2025-09-05 23:08:45.273425',NULL,'C','C',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (182,'Secção de Administração Pública e Trabalho','','',1,'2025-09-05 23:08:45.290586',NULL,'C','C',181);
INSERT INTO "ARQUIVOS_departamento" VALUES (183,'Secção de Registo Eleitoral, Recenseamento Militar e Organização do Território','','',1,'2025-09-05 23:08:45.304990',NULL,'C','C',181);
INSERT INTO "ARQUIVOS_departamento" VALUES (184,'Secção de Modernização Administrativa, e Gestão do Balcão Único de Atendimento ao Público (BUAP)','','',1,'2025-09-05 23:08:45.315900',NULL,'C','C',181);
INSERT INTO "ARQUIVOS_departamento" VALUES (185,'Secretaria Geral','','',1,'2025-09-05 23:08:45.326168',NULL,'E','E',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (186,'Gabinete Jurídico e Apoio às Comissões de Moradores','','',1,'2025-09-05 23:08:45.337730',NULL,'E','E',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (187,'Direcção Municipal da Educação','','',1,'2025-09-05 23:08:45.351887',NULL,'E','E',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (188,'Direcção Municipal da Saúde','','',1,'2025-09-05 23:08:45.363788',NULL,'E','E',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (189,'Direcção Municipal de Promoção do Desenvolvimento Económico Integrado','','',1,'2025-09-05 23:08:45.379433',NULL,'E','E',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (190,'Direção Municipal da Fiscalização e Inspecção das Actividades Económicas e Segurança Alimentar','','',1,'2025-09-05 23:08:45.396446',NULL,'E','E',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (191,'Direcção Municipal da Acção Social, Turismo, Cultura Juventude e Desportos','','',1,'2025-09-05 23:08:45.410310',NULL,'E','E',NULL);
INSERT INTO "ARQUIVOS_departamento" VALUES (192,'Direcção Municipal de Infra-estruturas, e Serviços Técnicos','','',1,'2025-09-05 23:08:45.428747',NULL,'E','E',NULL);
INSERT INTO "ARQUIVOS_documento" VALUES (18,'2025000001','Novo','gh','documentos/2025/09/brasas_lfycIm0.png','','aprovado','baixa','2025-09-07 22:36:31.151666','2025-10-07 22:36:31.149573','2025-09-08 10:52:49.517792','','',6,186,187,6,1);
INSERT INTO "ARQUIVOS_documento" VALUES (19,'2025000002','mais este','a','documentos/2025/09/brasas_IUxbQtT.png','','arquivado','normal','2025-09-07 22:42:13.917912','2025-10-07 22:42:13.916385','2025-09-08 10:17:35.213335','','',1,185,185,1,1);
INSERT INTO "ARQUIVOS_documento" VALUES (20,'2025000003','FILDA','dwe','','','encaminhamento','baixa','2025-09-07 22:44:48.730841','2025-10-07 22:44:48.730191','2025-09-08 10:30:55.198112','','',6,189,187,6,1);
INSERT INTO "ARQUIVOS_documento" VALUES (21,'2025000004','MINDCOM capacita quadros sobre licenciamento comercial','ewew','documentos/2025/09/brasas_TSZt0eg.png','','criacao','normal','2025-09-08 10:50:08.635484','2025-10-08 10:50:08.633803',NULL,'','',6,186,187,6,1);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (21,'despacho','2025-09-07 22:36:31.167567','Documento criado no sistema','',1,'2025-09-07 23:12:34.538931',NULL,186,18,6,6);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (22,'despacho','2025-09-07 22:42:13.939143','Documento criado no sistema','',0,NULL,185,186,19,1,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (23,'encaminhamento','2025-09-07 22:44:48.754197','Documento criado no sistema','',1,'2025-09-07 23:15:22.282701',185,186,20,6,1);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (24,'encaminhamento','2025-09-07 23:15:09.975627','','ret',1,'2025-09-07 23:58:43.836833',187,185,20,1,6);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (25,'despacho','2025-09-07 23:58:55.062833','','wr',0,NULL,NULL,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (26,'encaminhamento','2025-09-08 00:13:38.356206','','',1,'2025-09-08 00:15:04.874994',185,187,20,6,1);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (27,'encaminhamento','2025-09-08 00:15:29.793926','','',1,'2025-09-08 00:16:52.061033',187,185,20,1,3);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (28,'arquivado','2025-09-08 00:25:02.194177','Documento marcado como "Arquivado" por Alegria.','',0,NULL,NULL,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (29,'reprovado','2025-09-08 00:26:41.052968','Documento marcado como "Reprovado" por Alegria.','',0,NULL,NULL,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (30,'aprovado','2025-09-08 00:26:52.128964','Documento marcado como "Aprovado" por Alegria.','',0,NULL,NULL,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (31,'despacho','2025-09-08 00:34:31.859782','','FLATA X',0,NULL,NULL,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (32,'despacho','2025-09-08 10:14:28.551542','','sem parecer eficaz',0,NULL,NULL,185,19,1,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (33,'despacho','2025-09-08 10:17:35.202868','','vai techee',0,NULL,NULL,185,19,1,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (34,'despacho','2025-09-08 10:29:29.612407','','rt',0,NULL,NULL,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (35,'despacho','2025-09-08 10:30:35.009857','','não pode ser procedido porque falta x e y',0,NULL,NULL,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (36,'despacho','2025-09-08 10:30:55.179969','','ewwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwweeeeeeeeeeeeeeeeeeeee
weeeeeeeeeeeeee',0,NULL,NULL,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (37,'encaminhamento','2025-09-08 10:31:56.380807','na tem aver com esta area','',0,NULL,189,187,20,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (38,'criacao','2025-09-08 10:50:08.644883','Documento criado no sistema','',1,NULL,186,187,21,6,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (39,'despacho','2025-09-08 10:51:41.891596','','arquivamos porque n server pra nada',0,NULL,NULL,186,18,3,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (40,'despacho','2025-09-08 10:52:30.510192','','sssss',0,NULL,NULL,186,18,3,NULL);
INSERT INTO "ARQUIVOS_movimentacaodocumento" VALUES (41,'aprovado','2025-09-08 10:52:49.513447','Documento marcado como "Aprovado" por Fernando.','',0,NULL,NULL,186,18,3,NULL);
INSERT INTO "ARQUIVOS_notificacao" VALUES (1,'O documento ''2025000001'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/18','2025-09-07 22:40:25.596289',1,1);
INSERT INTO "ARQUIVOS_notificacao" VALUES (2,'O documento ''2025000001'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/18','2025-09-07 22:41:38.867629',1,6);
INSERT INTO "ARQUIVOS_notificacao" VALUES (3,'O documento ''2025000003'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-07 22:45:52.848815',1,3);
INSERT INTO "ARQUIVOS_notificacao" VALUES (4,'O documento ''2025000002'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/19','2025-09-07 22:46:30.650941',1,3);
INSERT INTO "ARQUIVOS_notificacao" VALUES (5,'O recebimento do documento ''2025000001'' foi confirmado por Alegria.','http://127.0.0.1:8000/documentos/detalhe/18','2025-09-07 23:12:34.561784',1,6);
INSERT INTO "ARQUIVOS_notificacao" VALUES (6,'O documento ''2025000003'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-07 23:13:33.288525',1,1);
INSERT INTO "ARQUIVOS_notificacao" VALUES (7,'O recebimento do documento ''2025000003'' foi confirmado por ruitunga.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-07 23:15:22.305565',1,6);
INSERT INTO "ARQUIVOS_notificacao" VALUES (8,'O documento ''2025000001'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/18','2025-09-07 23:22:36.692558',1,3);
INSERT INTO "ARQUIVOS_notificacao" VALUES (9,'O documento ''2025000003'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-07 23:54:59.284212',1,6);
INSERT INTO "ARQUIVOS_notificacao" VALUES (10,'O recebimento do documento ''2025000003'' foi confirmado por Alegria.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-07 23:58:43.860521',1,1);
INSERT INTO "ARQUIVOS_notificacao" VALUES (11,'O documento ''2025000003'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-08 00:13:38.383523',1,1);
INSERT INTO "ARQUIVOS_notificacao" VALUES (12,'O recebimento do documento ''2025000003'' foi confirmado por ruitunga.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-08 00:15:04.900152',1,6);
INSERT INTO "ARQUIVOS_notificacao" VALUES (13,'O documento ''2025000003'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-08 00:15:29.825989',1,3);
INSERT INTO "ARQUIVOS_notificacao" VALUES (14,'O recebimento do documento ''2025000003'' foi confirmado por Fernando.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-08 00:16:52.088890',1,1);
INSERT INTO "ARQUIVOS_notificacao" VALUES (15,'O documento ''2025000003'' foi encaminhado para o seu departamento.','http://127.0.0.1:8000/documentos/detalhe/20','2025-09-08 00:24:41.093380',1,6);
INSERT INTO "ARQUIVOS_notificacao" VALUES (16,'O seu documento ''2025000001'' foi finalizado com o status ''Aprovado''.','http://127.0.0.1:8000/documentos/detalhe/18','2025-09-08 10:52:49.532528',0,6);
INSERT INTO "ARQUIVOS_tipodocumento" VALUES (1,'Licenças e autorizações','',30,1);
INSERT INTO "ARQUIVOS_tipodocumento" VALUES (2,'Relatórios técnicos e inspeções','',30,1);
INSERT INTO "ARQUIVOS_tipodocumento" VALUES (3,'Correspondência oficial','',30,1);
INSERT INTO "ARQUIVOS_tipodocumento" VALUES (4,'Projetos e propostas de políticas','',30,1);
INSERT INTO "ARQUIVOS_tipodocumento" VALUES (5,'Contratos e protocolos','',30,1);
INSERT INTO "auth_group" VALUES (1,'Operador');
INSERT INTO "auth_group" VALUES (2,'Director');
INSERT INTO "auth_group_permissions" VALUES (1,1,42);
INSERT INTO "auth_group_permissions" VALUES (2,1,44);
INSERT INTO "auth_group_permissions" VALUES (3,2,1);
INSERT INTO "auth_group_permissions" VALUES (4,2,2);
INSERT INTO "auth_group_permissions" VALUES (5,2,3);
INSERT INTO "auth_group_permissions" VALUES (6,2,4);
INSERT INTO "auth_group_permissions" VALUES (7,2,5);
INSERT INTO "auth_group_permissions" VALUES (8,2,6);
INSERT INTO "auth_group_permissions" VALUES (9,2,7);
INSERT INTO "auth_group_permissions" VALUES (10,2,8);
INSERT INTO "auth_group_permissions" VALUES (11,2,9);
INSERT INTO "auth_group_permissions" VALUES (12,2,10);
INSERT INTO "auth_group_permissions" VALUES (13,2,11);
INSERT INTO "auth_group_permissions" VALUES (14,2,12);
INSERT INTO "auth_group_permissions" VALUES (15,2,13);
INSERT INTO "auth_group_permissions" VALUES (16,2,14);
INSERT INTO "auth_group_permissions" VALUES (17,2,15);
INSERT INTO "auth_group_permissions" VALUES (18,2,16);
INSERT INTO "auth_group_permissions" VALUES (19,2,17);
INSERT INTO "auth_group_permissions" VALUES (20,2,18);
INSERT INTO "auth_group_permissions" VALUES (21,2,19);
INSERT INTO "auth_group_permissions" VALUES (22,2,20);
INSERT INTO "auth_group_permissions" VALUES (23,2,21);
INSERT INTO "auth_group_permissions" VALUES (24,2,22);
INSERT INTO "auth_group_permissions" VALUES (25,2,23);
INSERT INTO "auth_group_permissions" VALUES (26,2,24);
INSERT INTO "auth_group_permissions" VALUES (27,2,25);
INSERT INTO "auth_group_permissions" VALUES (28,2,26);
INSERT INTO "auth_group_permissions" VALUES (29,2,27);
INSERT INTO "auth_group_permissions" VALUES (30,2,28);
INSERT INTO "auth_group_permissions" VALUES (31,2,29);
INSERT INTO "auth_group_permissions" VALUES (32,2,30);
INSERT INTO "auth_group_permissions" VALUES (33,2,31);
INSERT INTO "auth_group_permissions" VALUES (34,2,32);
INSERT INTO "auth_group_permissions" VALUES (35,2,33);
INSERT INTO "auth_group_permissions" VALUES (36,2,34);
INSERT INTO "auth_group_permissions" VALUES (37,2,35);
INSERT INTO "auth_group_permissions" VALUES (38,2,36);
INSERT INTO "auth_group_permissions" VALUES (39,2,37);
INSERT INTO "auth_group_permissions" VALUES (40,2,38);
INSERT INTO "auth_group_permissions" VALUES (41,2,39);
INSERT INTO "auth_group_permissions" VALUES (42,2,40);
INSERT INTO "auth_group_permissions" VALUES (43,2,41);
INSERT INTO "auth_group_permissions" VALUES (44,2,42);
INSERT INTO "auth_group_permissions" VALUES (45,2,43);
INSERT INTO "auth_group_permissions" VALUES (46,2,44);
INSERT INTO "auth_group_permissions" VALUES (47,2,45);
INSERT INTO "auth_group_permissions" VALUES (48,2,46);
INSERT INTO "auth_group_permissions" VALUES (49,2,47);
INSERT INTO "auth_group_permissions" VALUES (50,2,48);
INSERT INTO "auth_permission" VALUES (1,1,'add_logentry','Can add log entry');
INSERT INTO "auth_permission" VALUES (2,1,'change_logentry','Can change log entry');
INSERT INTO "auth_permission" VALUES (3,1,'delete_logentry','Can delete log entry');
INSERT INTO "auth_permission" VALUES (4,1,'view_logentry','Can view log entry');
INSERT INTO "auth_permission" VALUES (5,2,'add_permission','Can add permission');
INSERT INTO "auth_permission" VALUES (6,2,'change_permission','Can change permission');
INSERT INTO "auth_permission" VALUES (7,2,'delete_permission','Can delete permission');
INSERT INTO "auth_permission" VALUES (8,2,'view_permission','Can view permission');
INSERT INTO "auth_permission" VALUES (9,3,'add_group','Can add group');
INSERT INTO "auth_permission" VALUES (10,3,'change_group','Can change group');
INSERT INTO "auth_permission" VALUES (11,3,'delete_group','Can delete group');
INSERT INTO "auth_permission" VALUES (12,3,'view_group','Can view group');
INSERT INTO "auth_permission" VALUES (13,4,'add_contenttype','Can add content type');
INSERT INTO "auth_permission" VALUES (14,4,'change_contenttype','Can change content type');
INSERT INTO "auth_permission" VALUES (15,4,'delete_contenttype','Can delete content type');
INSERT INTO "auth_permission" VALUES (16,4,'view_contenttype','Can view content type');
INSERT INTO "auth_permission" VALUES (17,5,'add_session','Can add session');
INSERT INTO "auth_permission" VALUES (18,5,'change_session','Can change session');
INSERT INTO "auth_permission" VALUES (19,5,'delete_session','Can delete session');
INSERT INTO "auth_permission" VALUES (20,5,'view_session','Can view session');
INSERT INTO "auth_permission" VALUES (21,6,'add_configuracaosistema','Can add Configuração');
INSERT INTO "auth_permission" VALUES (22,6,'change_configuracaosistema','Can change Configuração');
INSERT INTO "auth_permission" VALUES (23,6,'delete_configuracaosistema','Can delete Configuração');
INSERT INTO "auth_permission" VALUES (24,6,'view_configuracaosistema','Can view Configuração');
INSERT INTO "auth_permission" VALUES (25,7,'add_departamento','Can add Departamento');
INSERT INTO "auth_permission" VALUES (26,7,'change_departamento','Can change Departamento');
INSERT INTO "auth_permission" VALUES (27,7,'delete_departamento','Can delete Departamento');
INSERT INTO "auth_permission" VALUES (28,7,'view_departamento','Can view Departamento');
INSERT INTO "auth_permission" VALUES (29,8,'add_documento','Can add Documento');
INSERT INTO "auth_permission" VALUES (30,8,'change_documento','Can change Documento');
INSERT INTO "auth_permission" VALUES (31,8,'delete_documento','Can delete Documento');
INSERT INTO "auth_permission" VALUES (32,8,'view_documento','Can view Documento');
INSERT INTO "auth_permission" VALUES (33,9,'add_tipodocumento','Can add Tipo de Documento');
INSERT INTO "auth_permission" VALUES (34,9,'change_tipodocumento','Can change Tipo de Documento');
INSERT INTO "auth_permission" VALUES (35,9,'delete_tipodocumento','Can delete Tipo de Documento');
INSERT INTO "auth_permission" VALUES (36,9,'view_tipodocumento','Can view Tipo de Documento');
INSERT INTO "auth_permission" VALUES (37,10,'add_customuser','Can add user');
INSERT INTO "auth_permission" VALUES (38,10,'change_customuser','Can change user');
INSERT INTO "auth_permission" VALUES (39,10,'delete_customuser','Can delete user');
INSERT INTO "auth_permission" VALUES (40,10,'view_customuser','Can view user');
INSERT INTO "auth_permission" VALUES (41,11,'add_movimentacaodocumento','Can add Movimentação');
INSERT INTO "auth_permission" VALUES (42,11,'change_movimentacaodocumento','Can change Movimentação');
INSERT INTO "auth_permission" VALUES (43,11,'delete_movimentacaodocumento','Can delete Movimentação');
INSERT INTO "auth_permission" VALUES (44,11,'view_movimentacaodocumento','Can view Movimentação');
INSERT INTO "auth_permission" VALUES (45,12,'add_anexo','Can add Anexo');
INSERT INTO "auth_permission" VALUES (46,12,'change_anexo','Can change Anexo');
INSERT INTO "auth_permission" VALUES (47,12,'delete_anexo','Can delete Anexo');
INSERT INTO "auth_permission" VALUES (48,12,'view_anexo','Can view Anexo');
INSERT INTO "auth_permission" VALUES (49,13,'add_notificacao','Can add Notificação');
INSERT INTO "auth_permission" VALUES (50,13,'change_notificacao','Can change Notificação');
INSERT INTO "auth_permission" VALUES (51,13,'delete_notificacao','Can delete Notificação');
INSERT INTO "auth_permission" VALUES (52,13,'view_notificacao','Can view Notificação');
INSERT INTO "django_admin_log" VALUES (1,'1','01 - DNI',1,'[{"added": {}}]',7,1,'2025-05-28 20:24:54.707826');
INSERT INTO "django_admin_log" VALUES (2,'1','ruitunga - Diretor',2,'[{"changed": {"fields": ["Nivel acesso", "Departamento"]}}]',10,1,'2025-05-28 20:25:01.338271');
INSERT INTO "django_admin_log" VALUES (3,'2','02 - DNCI',1,'[{"added": {}}]',7,1,'2025-05-28 20:25:27.082438');
INSERT INTO "django_admin_log" VALUES (4,'3','03 - DNCE',1,'[{"added": {}}]',7,1,'2025-05-28 20:25:41.547457');
INSERT INTO "django_admin_log" VALUES (5,'4','04 - DNAPN',1,'[{"added": {}}]',7,1,'2025-05-28 20:26:12.078846');
INSERT INTO "django_admin_log" VALUES (6,'2','Kajamba - Operador',1,'[{"added": {}}]',10,1,'2025-05-28 20:27:14.115204');
INSERT INTO "django_admin_log" VALUES (7,'2','Kajamba - Operador',2,'[{"changed": {"fields": ["User permissions"]}}]',10,1,'2025-05-28 20:27:32.881117');
INSERT INTO "django_admin_log" VALUES (8,'3','Fernando - Operador',1,'[{"added": {}}]',10,1,'2025-05-28 20:28:05.518803');
INSERT INTO "django_admin_log" VALUES (9,'3','Fernando - Operador',2,'[{"changed": {"fields": ["User permissions"]}}]',10,1,'2025-05-28 20:28:20.719895');
INSERT INTO "django_admin_log" VALUES (10,'4','Mauro - Operador',1,'[{"added": {}}]',10,1,'2025-05-28 20:28:47.084954');
INSERT INTO "django_admin_log" VALUES (11,'4','Mauro - Operador',2,'[{"changed": {"fields": ["User permissions"]}}]',10,1,'2025-05-28 20:29:09.666813');
INSERT INTO "django_admin_log" VALUES (12,'1','Licenças e autorizações',1,'[{"added": {}}]',9,1,'2025-05-28 20:30:34.041931');
INSERT INTO "django_admin_log" VALUES (13,'2','Relatórios técnicos e inspeções',1,'[{"added": {}}]',9,1,'2025-05-28 20:30:44.677219');
INSERT INTO "django_admin_log" VALUES (14,'3','Correspondência oficial',1,'[{"added": {}}]',9,1,'2025-05-28 20:30:53.749198');
INSERT INTO "django_admin_log" VALUES (15,'4','Projetos e propostas de políticas',1,'[{"added": {}}]',9,1,'2025-05-28 20:31:00.264060');
INSERT INTO "django_admin_log" VALUES (16,'5','Contratos e protocolos',1,'[{"added": {}}]',9,1,'2025-05-28 20:31:09.113922');
INSERT INTO "django_admin_log" VALUES (17,'5','0988778 - GEP',1,'[{"added": {}}]',7,1,'2025-08-26 20:38:03.417026');
INSERT INTO "django_admin_log" VALUES (18,'6','657676 - Secretaria Geral',1,'[{"added": {}}]',7,1,'2025-08-26 20:38:17.482137');
INSERT INTO "django_admin_log" VALUES (19,'7','098767 - Gabinete Juridico',1,'[{"added": {}}]',7,1,'2025-08-26 20:38:40.495659');
INSERT INTO "django_admin_log" VALUES (20,'5','FernandoMendes - Operador',1,'[{"added": {}}]',10,1,'2025-08-26 20:40:05.399590');
INSERT INTO "django_admin_log" VALUES (21,'6','Alegria - Operador',1,'[{"added": {}}]',10,1,'2025-08-26 20:41:25.458013');
INSERT INTO "django_admin_log" VALUES (22,'6','Alegria - Operador',2,'[]',10,1,'2025-08-26 20:41:30.446364');
INSERT INTO "django_admin_log" VALUES (23,'6','Alegria - Operador',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-08-26 21:02:01.234928');
INSERT INTO "django_admin_log" VALUES (24,'5','FernandoMendes - Operador',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-08-26 21:02:17.672333');
INSERT INTO "django_admin_log" VALUES (25,'5','FernandoMendes - Supervisor',2,'[{"changed": {"fields": ["Nivel acesso"]}}]',10,1,'2025-08-26 21:20:01.136312');
INSERT INTO "django_admin_log" VALUES (26,'8','090909 - seria fo dep juridi',1,'[{"added": {}}]',7,1,'2025-08-26 21:52:51.922287');
INSERT INTO "django_admin_log" VALUES (27,'6','Alegria - Operador',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-08-26 21:53:21.863145');
INSERT INTO "django_admin_log" VALUES (28,'3','2025000003 - Criação',3,'',11,1,'2025-09-05 23:08:00.898236');
INSERT INTO "django_admin_log" VALUES (29,'2','2025000002 - Encaminhamento',3,'',11,1,'2025-09-05 23:08:00.913039');
INSERT INTO "django_admin_log" VALUES (30,'1','2025000001 - Criação',3,'',11,1,'2025-09-05 23:08:00.926440');
INSERT INTO "django_admin_log" VALUES (31,'3','2025000003 - Documento de teste',3,'',8,1,'2025-09-05 23:08:23.483389');
INSERT INTO "django_admin_log" VALUES (32,'2','2025000002 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-05 23:08:23.504754');
INSERT INTO "django_admin_log" VALUES (33,'1','2025000001 - Solicitação de Espaço',3,'',8,1,'2025-09-05 23:08:23.525000');
INSERT INTO "django_admin_log" VALUES (34,'8','seria fo dep juridi (A)',3,'',7,1,'2025-09-05 23:08:30.988475');
INSERT INTO "django_admin_log" VALUES (35,'7','Gabinete Juridico (A)',3,'',7,1,'2025-09-05 23:08:30.998797');
INSERT INTO "django_admin_log" VALUES (36,'6','Secretaria Geral (A)',3,'',7,1,'2025-09-05 23:08:31.008174');
INSERT INTO "django_admin_log" VALUES (37,'5','GEP (A)',3,'',7,1,'2025-09-05 23:08:31.016434');
INSERT INTO "django_admin_log" VALUES (38,'4','DNAPN (A)',3,'',7,1,'2025-09-05 23:08:31.025382');
INSERT INTO "django_admin_log" VALUES (39,'3','DNCE (A)',3,'',7,1,'2025-09-05 23:08:31.039599');
INSERT INTO "django_admin_log" VALUES (40,'2','DNCI (A)',3,'',7,1,'2025-09-05 23:08:31.054832');
INSERT INTO "django_admin_log" VALUES (41,'1','DNI (A)',3,'',7,1,'2025-09-05 23:08:31.068764');
INSERT INTO "django_admin_log" VALUES (42,'1','ruitunga - Diretor',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-09-05 23:10:20.150396');
INSERT INTO "django_admin_log" VALUES (43,'6','Alegria - Operador',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-09-05 23:12:27.029768');
INSERT INTO "django_admin_log" VALUES (44,'6','Alegria - Operador',2,'[{"changed": {"fields": ["password"]}}]',10,1,'2025-09-05 23:12:43.404211');
INSERT INTO "django_admin_log" VALUES (45,'6','Alegria - Operador',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-09-05 23:15:51.827985');
INSERT INTO "django_admin_log" VALUES (46,'6','Alegria - Operador',2,'[{"changed": {"fields": ["User permissions"]}}]',10,1,'2025-09-06 15:26:20.286618');
INSERT INTO "django_admin_log" VALUES (47,'1','Operador',1,'[{"added": {}}]',3,1,'2025-09-06 15:38:25.297064');
INSERT INTO "django_admin_log" VALUES (48,'2','Director',1,'[{"added": {}}]',3,1,'2025-09-06 15:39:47.351452');
INSERT INTO "django_admin_log" VALUES (49,'1','ruitunga - Diretor',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-09-06 22:59:58.519077');
INSERT INTO "django_admin_log" VALUES (50,'6','Alegria - Operador',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-09-07 12:21:17.939277');
INSERT INTO "django_admin_log" VALUES (51,'12','2025000009 - Criação',3,'',11,1,'2025-09-07 12:23:36.888782');
INSERT INTO "django_admin_log" VALUES (52,'11','2025000008 - Criação',3,'',11,1,'2025-09-07 12:23:36.930628');
INSERT INTO "django_admin_log" VALUES (53,'10','2025000007 - Criação',3,'',11,1,'2025-09-07 12:23:36.954921');
INSERT INTO "django_admin_log" VALUES (54,'9','2025000006 - Criação',3,'',11,1,'2025-09-07 12:23:36.978155');
INSERT INTO "django_admin_log" VALUES (55,'8','2025000005 - Criação',3,'',11,1,'2025-09-07 12:23:36.998675');
INSERT INTO "django_admin_log" VALUES (56,'7','2025000004 - Criação',3,'',11,1,'2025-09-07 12:23:37.015769');
INSERT INTO "django_admin_log" VALUES (57,'6','2025000003 - Criação',3,'',11,1,'2025-09-07 12:23:37.032873');
INSERT INTO "django_admin_log" VALUES (58,'5','2025000002 - Criação',3,'',11,1,'2025-09-07 12:23:37.049797');
INSERT INTO "django_admin_log" VALUES (59,'4','2025000001 - Criação',3,'',11,1,'2025-09-07 12:23:37.066739');
INSERT INTO "django_admin_log" VALUES (60,'12','2025000009 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-07 12:23:46.216748');
INSERT INTO "django_admin_log" VALUES (61,'11','2025000008 - Novo',3,'',8,1,'2025-09-07 12:23:46.230260');
INSERT INTO "django_admin_log" VALUES (62,'10','2025000007 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-07 12:23:46.242854');
INSERT INTO "django_admin_log" VALUES (63,'9','2025000006 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-07 12:23:46.259703');
INSERT INTO "django_admin_log" VALUES (64,'8','2025000005 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-07 12:23:46.270452');
INSERT INTO "django_admin_log" VALUES (65,'7','2025000004 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-07 12:23:46.281110');
INSERT INTO "django_admin_log" VALUES (66,'6','2025000003 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-07 12:23:46.288944');
INSERT INTO "django_admin_log" VALUES (67,'5','2025000002 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-07 12:23:46.296021');
INSERT INTO "django_admin_log" VALUES (68,'4','2025000001 - Avaliação do Desenvolvimento de Culturas em Diferentes Condições de Solo',3,'',8,1,'2025-09-07 12:23:46.307064');
INSERT INTO "django_admin_log" VALUES (69,'3','Fernando - Operador',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-09-07 12:26:36.436161');
INSERT INTO "django_admin_log" VALUES (70,'3','Fernando - Operador',2,'[{"changed": {"fields": ["Groups"]}}]',10,1,'2025-09-07 12:27:42.142777');
INSERT INTO "django_admin_log" VALUES (71,'3','Fernando - Operador',2,'[{"changed": {"fields": ["password"]}}]',10,1,'2025-09-07 12:28:22.267700');
INSERT INTO "django_admin_log" VALUES (72,'6','Alegria - Operador',2,'[{"changed": {"fields": ["Groups"]}}]',10,1,'2025-09-07 12:34:09.094105');
INSERT INTO "django_admin_log" VALUES (73,'6','Alegria - Operador',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-09-07 12:39:51.196812');
INSERT INTO "django_admin_log" VALUES (74,'13','2025000001 - Consultoria em Fiscalidade',2,'[{"changed": {"fields": ["Criado por", "Responsavel atual"]}}]',8,1,'2025-09-07 18:54:24.780833');
INSERT INTO "django_admin_log" VALUES (75,'1','ruitunga - Diretor',2,'[{"changed": {"fields": ["Departamento"]}}]',10,1,'2025-09-07 18:59:54.698368');
INSERT INTO "django_admin_log" VALUES (76,'15','2025000003 - Novo teste',2,'[{"changed": {"fields": ["Status"]}}]',8,1,'2025-09-07 19:51:05.046825');
INSERT INTO "django_admin_log" VALUES (77,'15','2025000003 - Novo teste',3,'',8,1,'2025-09-07 21:02:11.624537');
INSERT INTO "django_admin_log" VALUES (78,'14','2025000002 - Novo teste',3,'',8,1,'2025-09-07 21:02:11.640343');
INSERT INTO "django_admin_log" VALUES (79,'13','2025000001 - Consultoria em Fiscalidade',3,'',8,1,'2025-09-07 21:02:11.652778');
INSERT INTO "django_admin_log" VALUES (80,'16','2025000001 - titulo de propriedade',2,'[{"changed": {"fields": ["Status"]}}]',8,1,'2025-09-07 21:07:40.442169');
INSERT INTO "django_admin_log" VALUES (81,'16','2025000001 - titulo de propriedade',2,'[{"changed": {"fields": ["Status"]}}]',8,1,'2025-09-07 21:11:08.774202');
INSERT INTO "django_admin_log" VALUES (82,'17','2025000002 - Solicitação de Espaço',3,'',8,1,'2025-09-07 22:36:05.490771');
INSERT INTO "django_admin_log" VALUES (83,'16','2025000001 - titulo de propriedade',3,'',8,1,'2025-09-07 22:36:05.500723');
INSERT INTO "django_content_type" VALUES (1,'admin','logentry');
INSERT INTO "django_content_type" VALUES (2,'auth','permission');
INSERT INTO "django_content_type" VALUES (3,'auth','group');
INSERT INTO "django_content_type" VALUES (4,'contenttypes','contenttype');
INSERT INTO "django_content_type" VALUES (5,'sessions','session');
INSERT INTO "django_content_type" VALUES (6,'ARQUIVOS','configuracaosistema');
INSERT INTO "django_content_type" VALUES (7,'ARQUIVOS','departamento');
INSERT INTO "django_content_type" VALUES (8,'ARQUIVOS','documento');
INSERT INTO "django_content_type" VALUES (9,'ARQUIVOS','tipodocumento');
INSERT INTO "django_content_type" VALUES (10,'ARQUIVOS','customuser');
INSERT INTO "django_content_type" VALUES (11,'ARQUIVOS','movimentacaodocumento');
INSERT INTO "django_content_type" VALUES (12,'ARQUIVOS','anexo');
INSERT INTO "django_content_type" VALUES (13,'ARQUIVOS','notificacao');
CREATE INDEX IF NOT EXISTS "ARQUIVOS_anexo_documento_id_a2883473" ON "ARQUIVOS_anexo" (
	"documento_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_anexo_usuario_upload_id_735884a2" ON "ARQUIVOS_anexo" (
	"usuario_upload_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_customuser_departamento_id_a9393ceb" ON "ARQUIVOS_customuser" (
	"departamento_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_customuser_groups_customuser_id_e1342cba" ON "ARQUIVOS_customuser_groups" (
	"customuser_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ARQUIVOS_customuser_groups_customuser_id_group_id_ca490418_uniq" ON "ARQUIVOS_customuser_groups" (
	"customuser_id",
	"group_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_customuser_groups_group_id_d20234ea" ON "ARQUIVOS_customuser_groups" (
	"group_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_customuser_user_permissions_customuser_id_a9b83ee8" ON "ARQUIVOS_customuser_user_permissions" (
	"customuser_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ARQUIVOS_customuser_user_permissions_customuser_id_permission_id_1840bf3e_uniq" ON "ARQUIVOS_customuser_user_permissions" (
	"customuser_id",
	"permission_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_customuser_user_permissions_permission_id_3d3ea054" ON "ARQUIVOS_customuser_user_permissions" (
	"permission_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ARQUIVOS_departamento_nome_parent_id_tipo_municipio_a03e2da1_uniq" ON "ARQUIVOS_departamento" (
	"nome",
	"parent_id",
	"tipo_municipio"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_departamento_parent_id_1da4beee" ON "ARQUIVOS_departamento" (
	"parent_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_departamento_responsavel_id_a83c8843" ON "ARQUIVOS_departamento" (
	"responsavel_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_documento_criado_por_id_ad1c7e9c" ON "ARQUIVOS_documento" (
	"criado_por_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_documento_departamento_atual_id_0d67b4ab" ON "ARQUIVOS_documento" (
	"departamento_atual_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_documento_departamento_origem_id_da74cc53" ON "ARQUIVOS_documento" (
	"departamento_origem_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_documento_responsavel_atual_id_2d4c5d0a" ON "ARQUIVOS_documento" (
	"responsavel_atual_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_documento_tipo_documento_id_51363d03" ON "ARQUIVOS_documento" (
	"tipo_documento_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_movimentacaodocumento_departamento_destino_id_66499a9c" ON "ARQUIVOS_movimentacaodocumento" (
	"departamento_destino_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_movimentacaodocumento_departamento_origem_id_2e567dde" ON "ARQUIVOS_movimentacaodocumento" (
	"departamento_origem_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_movimentacaodocumento_documento_id_7067a52f" ON "ARQUIVOS_movimentacaodocumento" (
	"documento_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_movimentacaodocumento_usuario_confirmacao_id_e0577adf" ON "ARQUIVOS_movimentacaodocumento" (
	"usuario_confirmacao_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_movimentacaodocumento_usuario_id_9778a640" ON "ARQUIVOS_movimentacaodocumento" (
	"usuario_id"
);
CREATE INDEX IF NOT EXISTS "ARQUIVOS_notificacao_usuario_id_2e2a488a" ON "ARQUIVOS_notificacao" (
	"usuario_id"
);
CREATE INDEX IF NOT EXISTS "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" (
	"group_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" (
	"group_id",
	"permission_id"
);
CREATE INDEX IF NOT EXISTS "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" (
	"permission_id"
);
CREATE INDEX IF NOT EXISTS "auth_permission_content_type_id_2f476e4b" ON "auth_permission" (
	"content_type_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" (
	"content_type_id",
	"codename"
);
CREATE INDEX IF NOT EXISTS "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" (
	"content_type_id"
);
CREATE INDEX IF NOT EXISTS "django_admin_log_user_id_c564eba6" ON "django_admin_log" (
	"user_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" (
	"app_label",
	"model"
);
COMMIT;
