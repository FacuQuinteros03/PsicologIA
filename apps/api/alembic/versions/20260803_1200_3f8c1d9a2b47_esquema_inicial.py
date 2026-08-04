"""esquema inicial

Revision ID: 3f8c1d9a2b47
Revises:
Create Date: 2026-08-03

"""
from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "3f8c1d9a2b47"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "terapeutas",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("nombre_completo", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column("matricula", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_terapeutas_email"), "terapeutas", ["email"], unique=True)

    op.create_table(
        "pacientes",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("terapeuta_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("apellido", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("telefono", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("motivo_consulta", sa.Text(), nullable=True),
        sa.Column(
            "estado",
            sa.Enum(
                "activo", "pausa", "alta", "archivado",
                name="ck_pacientes_estado", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "datos",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["terapeuta_id"], ["terapeutas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pacientes_terapeuta_id"), "pacientes", ["terapeuta_id"], unique=False)

    op.create_table(
        "nodos_genograma",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("etiqueta", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("nombre", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
        sa.Column(
            "rol",
            sa.Enum(
                "indice", "madre", "padre", "hermano", "pareja", "hijo", "abuelo",
                "tio", "amigo", "laboral", "terapeuta", "otro",
                name="ck_nodos_rol", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "genero",
            sa.Enum(
                "femenino", "masculino", "no_binario", "desconocido",
                name="ck_nodos_genero", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("fallecido", sa.Boolean(), nullable=False),
        sa.Column("fecha_fallecimiento", sa.Date(), nullable=True),
        sa.Column("pos_x", sa.Float(), nullable=False),
        sa.Column("pos_y", sa.Float(), nullable=False),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("es_indice", sa.Boolean(), nullable=False),
        sa.Column(
            "datos",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paciente_id", "etiqueta", name="uq_nodo_paciente_etiqueta"),
    )
    op.create_index(
        op.f("ix_nodos_genograma_paciente_id"), "nodos_genograma", ["paciente_id"], unique=False
    )

    op.create_table(
        "sesiones",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_sesion", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("numero_sesion", sa.Integer(), nullable=True),
        sa.Column("notas_borrador", sa.Text(), nullable=False),
        sa.Column("resumen_ia", sa.Text(), nullable=True),
        sa.Column(
            "tags",
            sa.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("estado_emocional", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=True),
        sa.Column(
            "ia_estado",
            sa.Enum(
                "pendiente", "procesando", "completado", "error",
                name="ck_sesiones_ia_estado", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("ia_modelo", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("ia_procesado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ia_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sesiones_tags", "sesiones", ["tags"], unique=False, postgresql_using="gin")
    # Índice compuesto con orden descendente: el autogenerate no lo emite porque es
    # una expresión, hay que declararlo acá.
    op.create_index(
        "ix_sesiones_paciente_fecha",
        "sesiones",
        ["paciente_id", sa.text("fecha_sesion DESC")],
        unique=False,
    )
    # Búsqueda temática full-text en español. Va por `execute` porque Alembic no
    # compara índices de expresión de forma estable; `env.py` lo tiene en
    # INDICES_MANUALES para que el autogenerate no intente borrarlo.
    op.execute(
        """
        CREATE INDEX ix_sesiones_fts ON sesiones USING gin (
            to_tsvector(
                'spanish',
                coalesce(resumen_ia, '') || ' ' || coalesce(notas_borrador, '')
            )
        )
        """
    )

    op.create_table(
        "conexiones_genograma",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("origen_id", sa.Uuid(), nullable=False),
        sa.Column("destino_id", sa.Uuid(), nullable=False),
        sa.Column(
            "tipo_vinculo",
            sa.Enum(
                "filial", "parental", "pareja", "matrimonio", "separacion",
                "divorcio", "hermano", "amistad", "laboral", "otro",
                name="ck_conexiones_tipo_vinculo", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "calidad_vinculo",
            sa.Enum(
                "cercano", "distante", "conflictivo", "fusionado", "roto",
                "ambivalente", "neutral",
                name="ck_conexiones_calidad_vinculo", native_enum=False, create_constraint=True,
            ),
            nullable=True,
        ),
        sa.Column("etiqueta", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=True),
        sa.Column(
            "datos",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.CheckConstraint("origen_id <> destino_id", name="ck_conexion_no_autorreferente"),
        sa.ForeignKeyConstraint(["destino_id"], ["nodos_genograma.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["origen_id"], ["nodos_genograma.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "origen_id", "destino_id", "tipo_vinculo", name="uq_conexion_origen_destino_tipo"
        ),
    )
    op.create_index(
        op.f("ix_conexiones_genograma_destino_id"), "conexiones_genograma", ["destino_id"], unique=False
    )
    op.create_index(
        op.f("ix_conexiones_genograma_origen_id"), "conexiones_genograma", ["origen_id"], unique=False
    )
    op.create_index(
        op.f("ix_conexiones_genograma_paciente_id"), "conexiones_genograma", ["paciente_id"], unique=False
    )

    op.create_table(
        "recordatorios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sesion_id", sa.Uuid(), nullable=False),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column(
            "prioridad",
            sa.Enum(
                "baja", "media", "alta",
                name="ck_recordatorios_prioridad", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("resuelto", sa.Boolean(), nullable=False),
        sa.Column("resuelto_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sesion_id"], ["sesiones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recordatorios_paciente_id"), "recordatorios", ["paciente_id"], unique=False)
    op.create_index(
        "ix_recordatorios_pendientes",
        "recordatorios",
        ["paciente_id"],
        unique=False,
        postgresql_where=sa.text("resuelto = false"),
    )
    op.create_index(op.f("ix_recordatorios_sesion_id"), "recordatorios", ["sesion_id"], unique=False)

    op.create_table(
        "sesion_nodo",
        sa.Column("sesion_id", sa.Uuid(), nullable=False),
        sa.Column("nodo_id", sa.Uuid(), nullable=False),
        sa.Column("menciones", sa.Integer(), nullable=False),
        sa.Column("contexto", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["nodo_id"], ["nodos_genograma.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sesion_id"], ["sesiones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("sesion_id", "nodo_id"),
    )
    op.create_index(op.f("ix_sesion_nodo_nodo_id"), "sesion_nodo", ["nodo_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sesion_nodo_nodo_id"), table_name="sesion_nodo")
    op.drop_table("sesion_nodo")

    op.drop_index(op.f("ix_recordatorios_sesion_id"), table_name="recordatorios")
    op.drop_index(
        "ix_recordatorios_pendientes",
        table_name="recordatorios",
        postgresql_where=sa.text("resuelto = false"),
    )
    op.drop_index(op.f("ix_recordatorios_paciente_id"), table_name="recordatorios")
    op.drop_table("recordatorios")

    op.drop_index(op.f("ix_conexiones_genograma_paciente_id"), table_name="conexiones_genograma")
    op.drop_index(op.f("ix_conexiones_genograma_origen_id"), table_name="conexiones_genograma")
    op.drop_index(op.f("ix_conexiones_genograma_destino_id"), table_name="conexiones_genograma")
    op.drop_table("conexiones_genograma")

    op.execute("DROP INDEX IF EXISTS ix_sesiones_fts")
    op.drop_index("ix_sesiones_paciente_fecha", table_name="sesiones")
    op.drop_index("ix_sesiones_tags", table_name="sesiones", postgresql_using="gin")
    op.drop_table("sesiones")

    op.drop_index(op.f("ix_nodos_genograma_paciente_id"), table_name="nodos_genograma")
    op.drop_table("nodos_genograma")

    op.drop_index(op.f("ix_pacientes_terapeuta_id"), table_name="pacientes")
    op.drop_table("pacientes")

    op.drop_index(op.f("ix_terapeutas_email"), table_name="terapeutas")
    op.drop_table("terapeutas")
