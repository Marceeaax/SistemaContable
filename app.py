import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "agasociados"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASS", "")
)


def format_amount_display(valor, moneda="GS."):
    if valor is None or valor == "":
        return ""

    try:
        decimal_valor = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return str(valor)

    if (moneda or "GS.").upper() in ("GS.", "GS", "GUARANIES", "GUARANIES."):
        decimal_valor = decimal_valor.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{decimal_valor:,.0f}".replace(",", ".")

    decimal_valor = decimal_valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{decimal_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


app.jinja_env.globals["format_amount_display"] = format_amount_display


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def decimal_form(valor, default="0"):
    texto = str(valor or default).strip()
    if not texto:
        texto = default

    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "." in texto:
        partes = texto.split(".")
        if len(partes) > 1 and len(partes[-1]) == 3:
            texto = "".join(partes)

    try:
        return Decimal(texto)
    except InvalidOperation:
        raise ValueError("Importe inválido")


def fetch_clientes():
    sql = """
        SELECT
            id_cliente,
            tipo_persona,
            nombre,
            ruc,
            dv,
            telefono,
            correo_set,
            contrasena_set,
            vencimiento
        FROM cliente
        ORDER BY nombre
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return cur.fetchall()


def fetch_persona_ref_por_numero(numero_cedula):
    sql = """
        SELECT
            COALESCE(rf_nombre, '') AS rf_nombre,
            COALESCE(rf_apellido, '') AS rf_apellido,
            rf_fecha_nac
        FROM personas_ref
        WHERE rf_numero = %s
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (numero_cedula,))
            return cur.fetchone()


def fetch_personas_ref_por_nombre_apellido(nombre="", apellido=""):
    filtros = []
    params = []

    if nombre:
        filtros.append("COALESCE(rf_nombre, '') ILIKE %s")
        params.append(f"%{nombre}%")

    if apellido:
        filtros.append("COALESCE(rf_apellido, '') ILIKE %s")
        params.append(f"%{apellido}%")

    if not filtros:
        return []

    sql = f"""
        SELECT
            rf_numero,
            COALESCE(rf_nombre, '') AS rf_nombre,
            COALESCE(rf_apellido, '') AS rf_apellido,
            rf_fecha_nac
        FROM personas_ref
        WHERE {' AND '.join(filtros)}
        ORDER BY rf_nombre, rf_apellido, rf_numero
        LIMIT 100
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def fetch_clientes_con_plan(excluir_id_cliente):
    sql = """
        SELECT
            c.id_cliente,
            c.nombre,
            COUNT(cc.id_cuenta) AS total_cuentas
        FROM cliente c
        JOIN cuenta_contable cc
          ON cc.id_cliente = c.id_cliente
        WHERE c.id_cliente <> %s
        GROUP BY c.id_cliente, c.nombre
        HAVING COUNT(cc.id_cuenta) > 0
        ORDER BY c.nombre
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (excluir_id_cliente,))
            return cur.fetchall()


def fetch_cliente_nombre(id_cliente):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nombre FROM cliente WHERE id_cliente = %s",
                (id_cliente,)
            )
            row = cur.fetchone()
    return row[0] if row else f"Cliente #{id_cliente}"


def fetch_asientos_cliente(id_cliente):
    sql = """
        SELECT
            a.id_asiento,
            a.fecha,
            a.descripcion,
            a.referencia,
            a.estado,
            a.numero_asiento,
            COUNT(al.id_linea) AS total_lineas,
            COALESCE(SUM(al.debe), 0) AS total_debe,
            COALESCE(SUM(al.haber), 0) AS total_haber
        FROM asiento a
        LEFT JOIN asiento_linea al
          ON al.id_asiento = a.id_asiento
         AND al.id_cliente = a.id_cliente
        WHERE a.id_cliente = %s
        GROUP BY a.id_asiento, a.fecha, a.descripcion, a.referencia, a.estado, a.numero_asiento
        ORDER BY a.numero_asiento DESC, a.id_asiento DESC
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (id_cliente,))
            return cur.fetchall()


def fetch_asiento_detalle(id_cliente, id_asiento):
    sql_asiento = """
        SELECT
            a.id_asiento,
            a.fecha,
            a.descripcion,
            a.referencia,
            a.estado,
            a.numero_asiento,
            a.tipo_asiento,
            EXISTS (
                SELECT 1
                FROM libro_iva_comprobante lic
                WHERE lic.id_cliente = a.id_cliente
                  AND lic.id_asiento = a.id_asiento
            ) AS es_libro_iva
        FROM asiento a
        WHERE a.id_cliente = %s
          AND a.id_asiento = %s
    """
    sql_lineas = """
        SELECT
            al.id_linea,
            al.id_cuenta,
            cc.codigo,
            cc.denominacion,
            al.glosa,
            al.debe,
            al.haber,
            EXISTS (
                SELECT 1
                FROM libro_iva_comprobante lic
                WHERE lic.id_cliente = al.id_cliente
                  AND lic.id_asiento = al.id_asiento
            ) AS es_libro_iva
        FROM asiento_linea al
        JOIN cuenta_contable cc
          ON cc.id_cliente = al.id_cliente
         AND cc.id_cuenta = al.id_cuenta
        WHERE al.id_cliente = %s
          AND al.id_asiento = %s
        ORDER BY al.id_linea
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql_asiento, (id_cliente, id_asiento))
            asiento = cur.fetchone()

            if not asiento:
                return None, []

            cur.execute(sql_lineas, (id_cliente, id_asiento))
            lineas = cur.fetchall()

    return asiento, lineas


def fetch_tipo_asiento(id_cliente, id_asiento):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tipo_asiento
                FROM asiento
                WHERE id_cliente = %s
                  AND id_asiento = %s
            """, (id_cliente, id_asiento))
            row = cur.fetchone()

    return row[0] if row else None


def fetch_cuentas_imputables(id_cliente):
    sql = """
        SELECT id_cuenta, codigo, denominacion
        FROM cuenta_contable
        WHERE id_cliente = %s
          AND imputable = true
          AND COALESCE(en_uso, true) = true
        ORDER BY codigo
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (id_cliente,))
            return cur.fetchall()


def cuenta_imputable_existe(id_cliente, id_cuenta):
    if not id_cuenta:
        return False

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM cuenta_contable
                WHERE id_cliente = %s
                  AND id_cuenta = %s
                  AND imputable = true
                  AND COALESCE(en_uso, true) = true
                LIMIT 1
            """, (id_cliente, id_cuenta))
            return cur.fetchone() is not None


def fetch_tipos_documento(libro):
    sql = """
        SELECT id_tipo_documento, codigo, descripcion, aplica_libro
        FROM tipo_documento
        WHERE activo = true
          AND aplica_libro IN (%s, 'AMBOS')
        ORDER BY codigo
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (libro,))
            return cur.fetchall()


def fetch_tipos_iva(libro):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'tipo_iva'
            """)
            columnas = {row["column_name"] for row in cur.fetchall()}

            select_extra = []
            if "cuenta_iva_5_codigo" in columnas:
                select_extra.append("cuenta_iva_5_codigo")
            else:
                select_extra.append("NULL::varchar AS cuenta_iva_5_codigo")

            if "cuenta_iva_10_codigo" in columnas:
                select_extra.append("cuenta_iva_10_codigo")
            else:
                select_extra.append("NULL::varchar AS cuenta_iva_10_codigo")

            if "incluido" in columnas:
                select_extra.append("incluido")
            else:
                select_extra.append("false AS incluido")

            sql = f"""
                SELECT id_tipo_iva, denominacion, {', '.join(select_extra)}
                FROM tipo_iva
                WHERE activo = true
                  AND aplica_libro = %s
                ORDER BY denominacion
            """
            cur.execute(sql, (libro,))
            return cur.fetchall()


def fetch_libro_iva_comprobantes(id_cliente, tipo_libro):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'libro_iva_comprobante'
            """)
            if not cur.fetchone():
                return []

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    lic.id_comprobante_iva,
                    lic.id_asiento,
                    a.numero_asiento,
                    lic.fecha,
                    lic.id_tipo_documento,
                    lic.id_tipo_iva,
                    lic.condicion,
                    td.codigo AS documento_codigo,
                    lic.numero_comprobante,
                    lic.ruc,
                    lic.razon_social,
                    lic.id_cuenta,
                    cc1.codigo AS cuenta_codigo,
                    cc1.denominacion AS cuenta_nombre,
                    lic.id_cta_iva_5,
                    cc5.codigo AS cta_iva_5_codigo,
                    cc5.denominacion AS cta_iva_5_nombre,
                    lic.id_cta_iva_10,
                    cc10.codigo AS cta_iva_10_codigo,
                    cc10.denominacion AS cta_iva_10_nombre,
                    lic.id_contracuenta,
                    ccc.codigo AS contracuenta_codigo,
                    ccc.denominacion AS contracuenta_nombre,
                    lic.detalle,
                    lic.exento,
                    lic.gravado_5,
                    lic.iva_5,
                    lic.gravado_10,
                    lic.iva_10,
                    lic.total,
                    lic.moneda,
                    lic.tipo_cambio,
                    ti.denominacion AS tipo_iva_denominacion
                FROM libro_iva_comprobante lic
                JOIN asiento a
                  ON a.id_asiento = lic.id_asiento
                 AND a.id_cliente = lic.id_cliente
                LEFT JOIN tipo_documento td
                  ON td.id_tipo_documento = lic.id_tipo_documento
                LEFT JOIN tipo_iva ti
                  ON ti.id_tipo_iva = lic.id_tipo_iva
                LEFT JOIN cuenta_contable cc1
                  ON cc1.id_cliente = lic.id_cliente
                 AND cc1.id_cuenta = lic.id_cuenta
                LEFT JOIN cuenta_contable cc5
                  ON cc5.id_cliente = lic.id_cliente
                 AND cc5.id_cuenta = lic.id_cta_iva_5
                LEFT JOIN cuenta_contable cc10
                  ON cc10.id_cliente = lic.id_cliente
                 AND cc10.id_cuenta = lic.id_cta_iva_10
                LEFT JOIN cuenta_contable ccc
                  ON ccc.id_cliente = lic.id_cliente
                 AND ccc.id_cuenta = lic.id_contracuenta
                WHERE lic.id_cliente = %s
                  AND lic.tipo_libro = %s
                ORDER BY a.numero_asiento, lic.fecha, lic.id_comprobante_iva
            """, (id_cliente, tipo_libro))
            return cur.fetchall()


def fetch_proximo_numero_asiento(id_cliente):
    sql = """
        SELECT COALESCE(MAX(numero_asiento), 0) + 1
        FROM asiento
        WHERE id_cliente = %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id_cliente,))
            return cur.fetchone()[0]


def procesar_lineas_asiento(id_cliente, cuentas_ids, glosas, debes, haberes):
    lineas = []
    total_debe = Decimal("0")
    total_haber = Decimal("0")

    for index, id_cuenta in enumerate(cuentas_ids):
        id_cuenta = (id_cuenta or "").strip()
        glosa = (glosas[index] if index < len(glosas) else "").strip()
        debe_raw = (debes[index] if index < len(debes) else "").strip().replace(",", "")
        haber_raw = (haberes[index] if index < len(haberes) else "").strip().replace(",", "")

        if not id_cuenta and not debe_raw and not haber_raw and not glosa:
            continue

        if not id_cuenta:
            return None, f"La línea {index + 1} no tiene cuenta seleccionada"

        try:
            debe = Decimal(debe_raw or "0")
            haber = Decimal(haber_raw or "0")
        except InvalidOperation:
            return None, f"La línea {index + 1} tiene un importe inválido"

        if debe < 0 or haber < 0:
            return None, f"La línea {index + 1} tiene importes negativos"

        if (debe > 0 and haber > 0) or (debe == 0 and haber == 0):
            return None, f"La línea {index + 1} debe tener débito o crédito, pero no ambos"

        lineas.append({
            "id_cuenta": int(id_cuenta),
            "glosa": glosa,
            "debe": debe,
            "haber": haber,
        })
        total_debe += debe
        total_haber += haber

    if len(lineas) < 2:
        return None, "El asiento debe tener al menos dos líneas"

    if total_debe != total_haber:
        return None, "El asiento debe quedar balanceado"

    cuentas_validas = {cuenta["id_cuenta"] for cuenta in fetch_cuentas_imputables(id_cliente)}
    for linea in lineas:
        if linea["id_cuenta"] not in cuentas_validas:
            return None, "Una de las cuentas seleccionadas no es válida para este cliente"

    return lineas, None


def crear_asiento_desde_form(id_cliente, tipo_asiento, solo_si_no_existen=False):
    numero_asiento_raw = request.form.get("numero_asiento", "").strip()
    fecha = request.form.get("fecha", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    referencia = request.form.get("referencia", "").strip().upper() or tipo_asiento

    cuentas_ids = request.form.getlist("linea_id_cuenta[]")
    glosas = request.form.getlist("linea_glosa[]")
    debes = request.form.getlist("linea_debe[]")
    haberes = request.form.getlist("linea_haber[]")

    if not fecha:
        return None, "La fecha del asiento es obligatoria"

    if not descripcion:
        return None, "El concepto del asiento es obligatorio"

    numero_asiento_solicitado = None
    if numero_asiento_raw:
        try:
            numero_asiento_solicitado = int(numero_asiento_raw)
        except ValueError:
            return None, "El número de asiento no es válido"

        if numero_asiento_solicitado <= 0:
            return None, "El número de asiento debe ser mayor a cero"

    lineas, error = procesar_lineas_asiento(id_cliente, cuentas_ids, glosas, debes, haberes)
    if error:
        return None, error

    referencia = tipo_asiento if solo_si_no_existen else referencia
    tipo_asiento_db = tipo_asiento if tipo_asiento in ("COMPRA", "VENTA") else "DIARIO"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM asiento WHERE id_cliente = %s LIMIT 1",
                (id_cliente,)
            )
            existe_asiento = cur.fetchone() is not None

            if solo_si_no_existen and existe_asiento:
                return None, "El cliente ya tiene asientos cargados"

            if numero_asiento_solicitado is None:
                cur.execute(
                    "SELECT COALESCE(MAX(numero_asiento), 0) + 1 FROM asiento WHERE id_cliente = %s",
                    (id_cliente,)
                )
                numero_asiento = cur.fetchone()[0]
            else:
                cur.execute(
                    "SELECT 1 FROM asiento WHERE id_cliente = %s AND numero_asiento = %s LIMIT 1",
                    (id_cliente, numero_asiento_solicitado)
                )
                if cur.fetchone() is not None:
                    return None, f"Ya existe el asiento número {numero_asiento_solicitado} para este cliente"
                numero_asiento = numero_asiento_solicitado

            cur.execute("""
                INSERT INTO asiento (id_cliente, numero_asiento, fecha, descripcion, referencia, estado, tipo_asiento)
                VALUES (%s, %s, %s, %s, %s, 'BORRADOR', %s)
                RETURNING id_asiento
            """, (id_cliente, numero_asiento, fecha, descripcion, referencia, tipo_asiento_db))
            id_asiento = cur.fetchone()[0]

            for linea in lineas:
                cur.execute("""
                    INSERT INTO asiento_linea
                    (id_asiento, id_cliente, id_cuenta, glosa, debe, haber)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    id_asiento,
                    id_cliente,
                    linea["id_cuenta"],
                    linea["glosa"] or None,
                    linea["debe"],
                    linea["haber"],
                ))

            conn.commit()

    return id_asiento, None


@app.route("/")
def index():
    clientes = fetch_clientes()
    return render_template("index.html", clientes=clientes)


@app.route("/bases-datos")
def bases_datos():
    return render_template("bases_datos.html")


@app.route("/bases-datos/consulta-personas")
def consulta_personas_ref():
    numero_cedula = request.args.get("numero_cedula", "").strip()

    if not numero_cedula:
        return jsonify({"ok": False, "error": "Debe ingresar un número de cédula"}), 400

    persona = fetch_persona_ref_por_numero(numero_cedula)
    if not persona:
        return jsonify({"ok": True, "persona": None})

    fecha_nac = persona["rf_fecha_nac"]
    return jsonify({
        "ok": True,
        "persona": {
            "nombre": persona["rf_nombre"] or "",
            "apellido": persona["rf_apellido"] or "",
            "fecha_nac": fecha_nac.strftime("%Y-%m-%d") if fecha_nac else ""
        }
    })


@app.route("/bases-datos/consulta-personas/buscar")
def buscar_personas_ref_por_nombre_apellido():
    nombre = request.args.get("nombre", "").strip()
    apellido = request.args.get("apellido", "").strip()

    if not nombre and not apellido:
        return jsonify({"ok": False, "error": "Debe ingresar nombre, apellido o ambos"}), 400

    personas = fetch_personas_ref_por_nombre_apellido(nombre, apellido)
    resultados = [
        {
            "numero": persona["rf_numero"] or "",
            "nombre": persona["rf_nombre"] or "",
            "apellido": persona["rf_apellido"] or "",
            "fecha_nac": persona["rf_fecha_nac"].strftime("%Y-%m-%d") if persona["rf_fecha_nac"] else ""
        }
        for persona in personas
    ]

    return jsonify({"ok": True, "personas": resultados})


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").lower().strip()
    password = request.form.get("password", "").strip()

    sql = """
        SELECT nombre
        FROM usuario
        WHERE username = %s
          AND password = %s
          AND activo = true
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (username, password))
            row = cur.fetchone()

    if row:
        session["logged_in"] = True
        session["username"] = row[0]
        flash(f"Bienvenido {row[0]}", "success")
    else:
        flash("Usuario o contraseña incorrectos", "danger")

    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("index"))

@app.route("/cliente/<int:id_cliente>/contabilidad")
def contabilidad_cliente(id_cliente):
    cliente_nombre = fetch_cliente_nombre(id_cliente)

    return render_template(
        "contabilidad.html",
        id_cliente=id_cliente,
        cliente_nombre=cliente_nombre
    )

@app.route("/cliente/<int:id_cliente>/contabilidad/asiento-diario")
def asiento_diario(id_cliente):
    cliente_nombre = fetch_cliente_nombre(id_cliente)
    asientos = fetch_asientos_cliente(id_cliente)
    cuentas = fetch_cuentas_imputables(id_cliente)
    nuevo = request.args.get("nuevo") == "1"
    tipo_nuevo = request.args.get("tipo", "").strip().upper() or ("APERTURA" if not asientos else "DIARIO")
    proximo_numero_asiento = fetch_proximo_numero_asiento(id_cliente)

    id_asiento = request.args.get("id_asiento", type=int)
    asiento_actual = None
    lineas = []

    if asientos:
        id_asiento = id_asiento or asientos[0]["id_asiento"]
        asiento_actual, lineas = fetch_asiento_detalle(id_cliente, id_asiento)

        if asiento_actual is None:
            asiento_actual, lineas = fetch_asiento_detalle(
                id_cliente,
                asientos[0]["id_asiento"]
            )

    total_debe = sum((linea["debe"] for linea in lineas), Decimal("0"))
    total_haber = sum((linea["haber"] for linea in lineas), Decimal("0"))

    return render_template(
        "contabilidad_asiento_diario.html",
        id_cliente=id_cliente,
        cliente_nombre=cliente_nombre,
        asientos=asientos,
        asiento_actual=asiento_actual,
        lineas=lineas,
        cuentas=cuentas,
        total_debe=total_debe,
        total_haber=total_haber,
        mostrar_alerta_apertura=not asientos and not nuevo,
        nuevo=nuevo,
        tipo_nuevo=tipo_nuevo,
        proximo_numero_asiento=proximo_numero_asiento
    )


@app.route("/cliente/<int:id_cliente>/contabilidad/asiento-apertura", methods=["POST"])
def crear_asiento_apertura(id_cliente):
    id_asiento, error = crear_asiento_desde_form(id_cliente, "APERTURA", solo_si_no_existen=True)
    if error:
        flash(error, "danger")
        return redirect(url_for("asiento_diario", id_cliente=id_cliente, nuevo=1, tipo="APERTURA"))

    flash("Asiento de apertura creado correctamente", "success")
    return redirect(url_for("asiento_diario", id_cliente=id_cliente, id_asiento=id_asiento))


@app.route("/cliente/<int:id_cliente>/contabilidad/asiento-guardar", methods=["POST"])
def guardar_asiento_diario(id_cliente):
    tipo_asiento = request.form.get("tipo_asiento", "DIARIO").strip().upper() or "DIARIO"
    solo_si_no_existen = tipo_asiento == "APERTURA"

    id_asiento, error = crear_asiento_desde_form(
        id_cliente,
        tipo_asiento,
        solo_si_no_existen=solo_si_no_existen
    )
    if error:
        flash(error, "danger")
        return redirect(url_for("asiento_diario", id_cliente=id_cliente, nuevo=1, tipo=tipo_asiento))

    flash("Asiento guardado correctamente", "success")
    return redirect(url_for("asiento_diario", id_cliente=id_cliente, id_asiento=id_asiento))


@app.route("/cliente/guardar", methods=["POST"])
def guardar_cliente():
    if not session.get("logged_in"):
        flash("Debe iniciar sesión", "danger")
        return redirect(url_for("index"))

    id_cliente = request.form.get("id_cliente")
    nombre = request.form.get("nombre")
    ruc = request.form.get("ruc")
    tipo_persona = request.form.get("tipo_persona")
    telefono = request.form.get("telefono")
    correo_set = request.form.get("correo_set")
    contrasena_set = request.form.get("contrasena_set")
    vencimiento_raw = request.form.get("vencimiento")
    vencimiento = int(vencimiento_raw) if vencimiento_raw else None

    # separar RUC y DV
    ruc_num, dv = ruc.split("-") if "-" in ruc else (ruc, None)

    with get_conn() as conn:
        with conn.cursor() as cur:

            if id_cliente:
                # UPDATE
                sql = """
                    UPDATE cliente
                    SET nombre = %s,
                        tipo_persona = %s,
                        ruc = %s,
                        dv = %s,
                        telefono = %s,
                        correo_set = %s,
                        contrasena_set = %s,
                        vencimiento = %s
                    WHERE id_cliente = %s
                """
                cur.execute(sql, (
                    nombre, tipo_persona, ruc_num, dv,
                    telefono, correo_set, contrasena_set,
                    vencimiento, id_cliente
                ))
                flash("Cliente actualizado correctamente", "success")

            else:
                # INSERT
                sql = """
                    INSERT INTO cliente
                    (nombre, tipo_persona, ruc, dv, telefono,
                     correo_set, contrasena_set, vencimiento)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cur.execute(sql, (
                    nombre, tipo_persona, ruc_num, dv,
                    telefono, correo_set, contrasena_set,
                    vencimiento
                ))
                flash("Cliente creado correctamente", "success")

    return redirect(url_for("index"))

@app.route("/cliente/<int:id_cliente>/contabilidad/plan-cuentas")
def plan_cuentas(id_cliente):

    sql = """
        WITH RECURSIVE arbol AS (
            SELECT
                id_cuenta,
                codigo,
                denominacion,
                alias,
                categoria,
                imputable,
                id_cuenta_madre,
                cuenta_r173,
                denom_r173,
                0 AS profundidad
            FROM cuenta_contable
            WHERE id_cliente = %s
              AND id_cuenta_madre IS NULL

            UNION ALL

            SELECT
                c.id_cuenta,
                c.codigo,
                c.denominacion,
                c.alias,
                c.categoria,
                c.imputable,
                c.id_cuenta_madre,
                c.cuenta_r173,
                c.denom_r173,
                a.profundidad + 1
            FROM cuenta_contable c
            JOIN arbol a
              ON c.id_cuenta_madre = a.id_cuenta
        )
        SELECT *
        FROM arbol
        ORDER BY codigo;
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id_cliente,))
            cuentas = cur.fetchall()

    clientes_origen = fetch_clientes_con_plan(id_cliente)

    return render_template(
        "contabilidad_plan.html",
        id_cliente=id_cliente,
        cuentas=cuentas,
        sin_cuentas=len(cuentas) == 0,
        clientes_origen=clientes_origen
    )

def get_cuentas(id_cliente):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id_cuenta, codigo, denominacion, alias,
                       categoria, imputable, id_cuenta_madre,
                       cuenta_r173, denom_r173, 0
                FROM cuenta_contable
                WHERE id_cliente = %s
                ORDER BY codigo
            """, (id_cliente,))
            return cur.fetchall()


@app.route("/cliente/<int:id_cliente>/plan-cuentas/nueva", methods=["POST"])
def nueva_cuenta(id_cliente):

    id_cuenta = request.form.get("id_cuenta")
    codigo = request.form.get("codigo", "").strip()
    denominacion = request.form.get("denominacion", "").strip()
    alias = request.form.get("alias")
    imputable = request.form.get("imputable") == "true"
    id_madre = request.form.get("id_cuenta_madre") or None
    forzar = request.form.get("forzar") == "1"

    if not codigo.isdigit():
        flash("El código debe ser numérico", "danger")
        return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

    if not denominacion:
        flash("La denominación es obligatoria", "danger")
        return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

    with get_conn() as conn:
        with conn.cursor() as cur:

            # ================================
            # 🔵 MODO EDICIÓN
            # ================================
            if id_cuenta:

                # Verificar movimientos
                cur.execute("""
                    SELECT 1 FROM asiento_linea
                    WHERE id_cuenta = %s
                    LIMIT 1
                """, (id_cuenta,))
                tiene_mov = cur.fetchone()

                # Obtener datos actuales
                cur.execute("""
                    SELECT codigo, imputable, id_cuenta_madre
                    FROM cuenta_contable
                    WHERE id_cuenta = %s
                """, (id_cuenta,))
                actual = cur.fetchone()

                if not actual:
                    flash("Cuenta no encontrada", "danger")
                    return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

                codigo_actual, imputable_actual, madre_actual = actual

                # Bloquear cambios estructurales si tiene movimientos
                if tiene_mov:
                    if (codigo != codigo_actual or
                        imputable != imputable_actual or
                        str(id_madre) != str(madre_actual)):
                        flash("No se puede modificar estructura de una cuenta con movimientos", "danger")
                        return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

                # 🔹 NUEVO BLOQUE
                if (codigo == codigo_actual and
                    imputable == imputable_actual and
                    str(id_madre) == str(madre_actual)):

                    flash("No se realizaron cambios", "info")
                    return redirect(url_for("plan_cuentas", id_cliente=id_cliente))
                
                # Recalcular categoría
                if id_madre:
                    cur.execute("""
                        SELECT categoria, imputable
                        FROM cuenta_contable
                        WHERE id_cuenta = %s AND id_cliente = %s
                    """, (id_madre, id_cliente))
                    padre = cur.fetchone()

                    if not padre:
                        flash("Cuenta madre no válida", "danger")
                        return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

                    categoria_padre, padre_imputable = padre

                    if padre_imputable:
                        flash("No se puede asignar como madre una cuenta imputable", "danger")
                        return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

                    categoria = categoria_padre + 1
                else:
                    categoria = 0

                # UPDATE
                cur.execute("""
                    UPDATE cuenta_contable
                    SET codigo=%s,
                        denominacion=%s,
                        alias=%s,
                        categoria=%s,
                        imputable=%s,
                        id_cuenta_madre=%s
                    WHERE id_cuenta=%s
                """, (
                    codigo,
                    denominacion,
                    alias,
                    categoria,
                    imputable,
                    id_madre,
                    id_cuenta
                ))

                conn.commit()
                flash("Cuenta actualizada correctamente", "success")
                return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

            # ================================
            # 🔵 MODO CREACIÓN
            # ================================

            # Validar código único
            cur.execute("""
                SELECT 1 FROM cuenta_contable
                WHERE id_cliente = %s AND codigo = %s
            """, (id_cliente, codigo))

            if cur.fetchone():
                flash("Ya existe una cuenta con ese código", "danger")
                return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

            # Validación similitud
            if not forzar:
                cur.execute("""
                    SELECT codigo, denominacion,
                           similarity(LOWER(denominacion), LOWER(%s)) AS sim
                    FROM cuenta_contable
                    WHERE id_cliente = %s
                      AND similarity(LOWER(denominacion), LOWER(%s)) > 0.75
                    ORDER BY sim DESC
                    LIMIT 1
                """, (denominacion, id_cliente, denominacion))

                similar = cur.fetchone()

                if similar:
                    codigo_sim, denom_sim, sim = similar

                    return render_template(
                        "contabilidad_plan.html",
                        id_cliente=id_cliente,
                        cuentas=get_cuentas(id_cliente),
                        sin_cuentas=False,
                        clientes_origen=fetch_clientes_con_plan(id_cliente),
                        confirmar_similitud=True,
                        cuenta_similar={
                            "codigo": codigo_sim,
                            "denominacion": denom_sim,
                            "similitud": float(sim),
                        },
                        codigo=codigo,
                        denominacion=denominacion,
                        alias=alias,
                        imputable=imputable,
                        id_madre=id_madre,
                        forzar=False
                    )

            # Validar padre
            if id_madre:
                cur.execute("""
                    SELECT categoria, imputable
                    FROM cuenta_contable
                    WHERE id_cuenta = %s AND id_cliente = %s
                """, (id_madre, id_cliente))

                padre = cur.fetchone()

                if not padre:
                    flash("Cuenta madre no válida", "danger")
                    return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

                categoria_padre, padre_imputable = padre

                if padre_imputable:
                    flash("No se puede agregar hijo a una cuenta imputable", "danger")
                    return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

                categoria = categoria_padre + 1
            else:
                categoria = 0

            # INSERT
            cur.execute("""
                INSERT INTO cuenta_contable
                (id_cliente, codigo, denominacion, alias,
                 categoria, imputable, id_cuenta_madre)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                id_cliente,
                codigo,
                denominacion,
                alias,
                categoria,
                imputable,
                id_madre
            ))

            conn.commit()

    flash("Cuenta creada correctamente", "success")
    return redirect(url_for("plan_cuentas", id_cliente=id_cliente))


@app.route("/cliente/<int:id_cliente>/plan-cuentas/importar", methods=["POST"])
def importar_plan_cuentas(id_cliente):
    id_cliente_origen = request.form.get("id_cliente_origen", type=int)

    if not id_cliente_origen or id_cliente_origen == id_cliente:
        flash("Debe seleccionar otro cliente como origen", "danger")
        return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM cuenta_contable
                WHERE id_cliente = %s
            """, (id_cliente,))
            total_destino = cur.fetchone()[0]

            if total_destino > 0:
                flash("El cliente ya tiene cuentas cargadas", "warning")
                return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

            cur.execute("""
                SELECT
                    id_cuenta,
                    codigo,
                    denominacion,
                    alias,
                    categoria,
                    imputable,
                    id_cuenta_madre,
                    cuenta_r173,
                    denom_r173,
                    COALESCE(en_uso, true)
                FROM cuenta_contable
                WHERE id_cliente = %s
                ORDER BY categoria, codigo, id_cuenta
            """, (id_cliente_origen,))
            cuentas_origen = cur.fetchall()

            if not cuentas_origen:
                flash("El cliente de origen no tiene cuentas para importar", "danger")
                return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

            mapa_cuentas = {}

            for cuenta in cuentas_origen:
                (
                    id_cuenta_origen,
                    codigo,
                    denominacion,
                    alias,
                    categoria,
                    imputable,
                    id_cuenta_madre,
                    cuenta_r173,
                    denom_r173,
                    en_uso,
                ) = cuenta

                nueva_madre = mapa_cuentas.get(id_cuenta_madre) if id_cuenta_madre else None

                cur.execute("""
                    INSERT INTO cuenta_contable
                    (
                        id_cliente,
                        codigo,
                        denominacion,
                        alias,
                        categoria,
                        imputable,
                        id_cuenta_madre,
                        cuenta_r173,
                        denom_r173,
                        en_uso
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id_cuenta
                """, (
                    id_cliente,
                    codigo,
                    denominacion,
                    alias,
                    categoria,
                    imputable,
                    nueva_madre,
                    cuenta_r173,
                    denom_r173,
                    en_uso,
                ))

                mapa_cuentas[id_cuenta_origen] = cur.fetchone()[0]

            conn.commit()

    flash("Plan de cuentas importado correctamente", "success")
    return redirect(url_for("plan_cuentas", id_cliente=id_cliente))


@app.route("/cliente/<int:id_cliente>/plan-cuentas/<int:id_cuenta>/eliminar", methods=["POST"])
def eliminar_cuenta(id_cliente, id_cuenta):

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT imputable
                FROM cuenta_contable
                WHERE id_cliente = %s
                  AND id_cuenta = %s
            """, (id_cliente, id_cuenta))
            cuenta = cur.fetchone()

            if not cuenta:
                flash("Cuenta no encontrada", "danger")
                return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

            imputable = cuenta[0]

            cur.execute("""
                SELECT 1
                FROM asiento_linea
                WHERE id_cliente = %s
                  AND id_cuenta = %s
                LIMIT 1
            """, (id_cliente, id_cuenta))
            if cur.fetchone():
                flash("No se puede eliminar una cuenta que tiene movimientos relacionados", "danger")
                return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

            if not imputable:
                cur.execute("""
                    SELECT 1
                    FROM cuenta_contable
                    WHERE id_cliente = %s
                      AND id_cuenta_madre = %s
                    LIMIT 1
                """, (id_cliente, id_cuenta))
                if cur.fetchone():
                    flash("No se puede eliminar una cuenta totalizadora que tiene subcuentas", "danger")
                    return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

            cur.execute("""
                DELETE FROM cuenta_contable
                WHERE id_cliente = %s
                  AND id_cuenta = %s
            """, (id_cliente, id_cuenta))

            conn.commit()

    flash("Cuenta eliminada correctamente", "success")
    return redirect(url_for("plan_cuentas", id_cliente=id_cliente))

@app.route("/cliente/<int:id_cliente>/contabilidad/libro-iva")
def libro_iva(id_cliente):
    nuevo = request.args.get("nuevo") == "1"
    id_asiento_seleccionado = request.args.get("id_asiento", type=int)
    tipo = request.args.get("tipo", "").strip().upper()

    if not tipo and id_asiento_seleccionado:
        tipo = (fetch_tipo_asiento(id_cliente, id_asiento_seleccionado) or "").strip().upper()

    if tipo not in ("COMPRA", "VENTA"):
        tipo = "COMPRA"

    tipos_documento = fetch_tipos_documento(tipo)
    tipos_iva = fetch_tipos_iva(tipo)
    comprobantes = fetch_libro_iva_comprobantes(id_cliente, tipo)

    return render_template(
        "contabilidad_libro_iva.html",
        id_cliente=id_cliente,
        nuevo=nuevo,
        tipo=tipo,
        id_asiento_seleccionado=id_asiento_seleccionado,
        tipos_documento=tipos_documento,
        tipos_iva=tipos_iva,
        comprobantes=comprobantes
    )


@app.route("/cliente/<int:id_cliente>/contabilidad/libro-iva/guardar", methods=["POST"])
def guardar_libro_iva(id_cliente):
    tipo_libro = request.form.get("tipo_libro", "COMPRA").strip().upper()
    id_comprobante_iva = request.form.get("id_comprobante_iva", type=int)
    if tipo_libro not in ("COMPRA", "VENTA"):
        return jsonify({"ok": False, "error": "Tipo de libro inválido"}), 400

    try:
        fecha = request.form.get("fecha", "").strip()
        id_tipo_documento = int(request.form.get("sigla") or 0)
        id_tipo_iva = int(request.form.get("id_tipo_iva") or 0)
        numero_comprobante = request.form.get("numero", "").strip()
        condicion = request.form.get("condicion", "").strip()
        ruc = request.form.get("ruc", "").strip()
        razon_social = request.form.get("nombre_razon", "").strip()
        detalle = request.form.get("detalle", "").strip()
        moneda = request.form.get("moneda", "GS.").strip()
        tipo_cambio = decimal_form(request.form.get("tipo_cambio", "1"), "1")

        id_cuenta = int(request.form.get("cuenta_id") or 0)
        id_cta_iva_5 = int(request.form.get("cta_iva_5_id") or 0) or None
        id_cta_iva_10 = int(request.form.get("cta_iva_10_id") or 0) or None
        id_contracuenta = int(request.form.get("contracuenta_id") or 0)

        exento = decimal_form(request.form.get("exento", "0"))
        gravado_5 = decimal_form(request.form.get("gravado_5", "0"))
        iva_5 = decimal_form(request.form.get("iva_5", "0"))
        gravado_10 = decimal_form(request.form.get("gravado_10", "0"))
        iva_10 = decimal_form(request.form.get("iva_10", "0"))
        total = decimal_form(request.form.get("total", "0"))
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "Datos inválidos en el comprobante"}), 400

    if not fecha:
        return jsonify({"ok": False, "error": "La fecha es obligatoria"}), 400
    try:
        fecha_comprobante = date.fromisoformat(fecha)
    except ValueError:
        return jsonify({"ok": False, "error": "La fecha no es válida"}), 400

    if fecha_comprobante > date.today():
        return jsonify({"ok": False, "error": "No se puede cargar una factura con fecha futura", "field": "fecha"}), 400

    if not numero_comprobante:
        return jsonify({"ok": False, "error": "El número de comprobante es obligatorio"}), 400
    if not id_tipo_documento:
        return jsonify({"ok": False, "error": "Debe seleccionar el tipo de comprobante"}), 400
    if not id_cuenta:
        return jsonify({"ok": False, "error": "Debe completar una cuenta válida", "field": "cuenta_codigo"}), 400
    if not id_contracuenta:
        return jsonify({"ok": False, "error": "Debe completar una contracuenta válida", "field": "contracuenta_codigo"}), 400
    if not cuenta_imputable_existe(id_cliente, id_cuenta):
        return jsonify({"ok": False, "error": "La cuenta no existe en el plan de cuentas de este cliente", "field": "cuenta_codigo"}), 400
    if not cuenta_imputable_existe(id_cliente, id_contracuenta):
        return jsonify({"ok": False, "error": "La contracuenta no existe en el plan de cuentas de este cliente", "field": "contracuenta_codigo"}), 400
    if iva_5 > 0 and not id_cta_iva_5:
        return jsonify({"ok": False, "error": "Debe completar la cuenta de IVA 5%", "field": "cta_iva_5_codigo"}), 400
    if iva_5 > 0 and not cuenta_imputable_existe(id_cliente, id_cta_iva_5):
        return jsonify({"ok": False, "error": "La cuenta de IVA 5% no existe en el plan de cuentas de este cliente", "field": "cta_iva_5_codigo"}), 400
    if iva_10 > 0 and not id_cta_iva_10:
        return jsonify({"ok": False, "error": "Debe completar la cuenta de IVA 10%", "field": "cta_iva_10_codigo"}), 400
    if iva_10 > 0 and not cuenta_imputable_existe(id_cliente, id_cta_iva_10):
        return jsonify({"ok": False, "error": "La cuenta de IVA 10% no existe en el plan de cuentas de este cliente", "field": "cta_iva_10_codigo"}), 400

    base = exento + gravado_5 + gravado_10
    total_calculado = base + iva_5 + iva_10
    if total == 0:
        total = total_calculado

    if total <= 0:
        return jsonify({"ok": False, "error": "El total debe ser mayor a cero"}), 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT codigo FROM tipo_documento WHERE id_tipo_documento = %s",
                (id_tipo_documento,)
            )
            row_tipo_documento = cur.fetchone()
            tipo_iva_denominacion = ""
            if id_tipo_iva:
                cur.execute(
                    "SELECT denominacion FROM tipo_iva WHERE id_tipo_iva = %s",
                    (id_tipo_iva,)
                )
                row_tipo_iva = cur.fetchone()
                tipo_iva_denominacion = row_tipo_iva[0] if row_tipo_iva else ""
    documento_codigo = row_tipo_documento[0] if row_tipo_documento else tipo_libro

    descripcion = detalle or f"{documento_codigo.title()} {numero_comprobante} {razon_social}".strip()
    referencia = tipo_libro

    lineas = []
    if tipo_libro == "COMPRA":
        lineas.append((id_cuenta, descripcion, Decimal("0"), total))
        if iva_5 > 0:
            lineas.append((id_cta_iva_5, descripcion, iva_5, Decimal("0")))
        if iva_10 > 0:
            lineas.append((id_cta_iva_10, descripcion, iva_10, Decimal("0")))
        if base > 0:
            lineas.append((id_contracuenta, descripcion, base, Decimal("0")))
    else:
        lineas.append((id_cuenta, descripcion, total, Decimal("0")))
        if base > 0:
            lineas.append((id_contracuenta, descripcion, Decimal("0"), base))
        if iva_5 > 0:
            lineas.append((id_cta_iva_5, descripcion, Decimal("0"), iva_5))
        if iva_10 > 0:
            lineas.append((id_cta_iva_10, descripcion, Decimal("0"), iva_10))

    total_debe = sum((linea[2] for linea in lineas), Decimal("0"))
    total_haber = sum((linea[3] for linea in lineas), Decimal("0"))
    if total_debe != total_haber:
        return jsonify({"ok": False, "error": "El asiento generado no queda balanceado"}), 400

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'libro_iva_comprobante'
                """)
                columnas = {row[0] for row in cur.fetchall()}
                if not columnas:
                    raise RuntimeError("No existe la tabla libro_iva_comprobante")

                if id_comprobante_iva:
                    cur.execute("""
                        SELECT id_asiento
                        FROM libro_iva_comprobante
                        WHERE id_cliente = %s
                          AND id_comprobante_iva = %s
                    """, (id_cliente, id_comprobante_iva))
                    row_existente = cur.fetchone()
                    if not row_existente:
                        return jsonify({"ok": False, "error": "No se encontró el comprobante a modificar"}), 404

                    id_asiento = row_existente[0]
                    cur.execute("""
                        SELECT numero_asiento
                        FROM asiento
                        WHERE id_cliente = %s
                          AND id_asiento = %s
                    """, (id_cliente, id_asiento))
                    numero_asiento = cur.fetchone()[0]

                    cur.execute("""
                        UPDATE asiento
                        SET fecha = %s,
                            descripcion = %s,
                            referencia = %s,
                            tipo_asiento = %s
                        WHERE id_cliente = %s
                          AND id_asiento = %s
                    """, (fecha, descripcion, referencia, tipo_libro, id_cliente, id_asiento))

                    cur.execute("""
                        DELETE FROM asiento_linea
                        WHERE id_cliente = %s
                          AND id_asiento = %s
                    """, (id_cliente, id_asiento))
                else:
                    cur.execute("""
                        SELECT COALESCE(MAX(numero_asiento), 0) + 1
                        FROM asiento
                        WHERE id_cliente = %s
                    """, (id_cliente,))
                    numero_asiento = cur.fetchone()[0]

                    cur.execute("""
                        INSERT INTO asiento
                        (id_cliente, numero_asiento, fecha, descripcion, referencia, estado, tipo_asiento)
                        VALUES (%s, %s, %s, %s, %s, 'BORRADOR', %s)
                        RETURNING id_asiento
                    """, (id_cliente, numero_asiento, fecha, descripcion, referencia, tipo_libro))
                    id_asiento = cur.fetchone()[0]

                for id_cuenta_linea, glosa, debe, haber in lineas:
                    cur.execute("""
                        INSERT INTO asiento_linea
                        (id_asiento, id_cliente, id_cuenta, glosa, debe, haber)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id_asiento, id_cliente, id_cuenta_linea, glosa, debe, haber))

                datos_comprobante = {
                    "id_cliente": id_cliente,
                    "id_asiento": id_asiento,
                    "tipo_libro": tipo_libro,
                    "id_tipo_documento": id_tipo_documento,
                    "id_tipo_iva": id_tipo_iva or None,
                    "fecha": fecha,
                    "condicion": condicion or None,
                    "numero_comprobante": numero_comprobante,
                    "ruc": ruc or None,
                    "razon_social": razon_social or None,
                    "id_cuenta": id_cuenta,
                    "id_cta_iva_5": id_cta_iva_5,
                    "id_cta_iva_10": id_cta_iva_10,
                    "id_contracuenta": id_contracuenta,
                    "detalle": detalle or None,
                    "moneda": moneda,
                    "tipo_cambio": tipo_cambio,
                    "exento": exento,
                    "gravado_5": gravado_5,
                    "iva_5": iva_5,
                    "gravado_10": gravado_10,
                    "iva_10": iva_10,
                    "total": total,
                    "estado": "BORRADOR",
                }
                datos_comprobante = {
                    columna: valor
                    for columna, valor in datos_comprobante.items()
                    if columna in columnas
                }

                columnas_insert = list(datos_comprobante.keys())
                placeholders = ", ".join(["%s"] * len(columnas_insert))
                valores_insert = [datos_comprobante[columna] for columna in columnas_insert]
                if id_comprobante_iva:
                    asignaciones = ", ".join(f"{columna} = %s" for columna in columnas_insert)
                    cur.execute(
                        f"""
                        UPDATE libro_iva_comprobante
                        SET {asignaciones}
                        WHERE id_cliente = %s
                          AND id_comprobante_iva = %s
                        """,
                        valores_insert + [id_cliente, id_comprobante_iva]
                    )
                else:
                    cur.execute(
                        f"""
                        INSERT INTO libro_iva_comprobante ({", ".join(columnas_insert)})
                        VALUES ({placeholders})
                        RETURNING id_comprobante_iva
                        """,
                        valores_insert
                    )
                    id_comprobante_iva = cur.fetchone()[0]

                conn.commit()
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    return jsonify({
        "ok": True,
        "id_asiento": id_asiento,
        "numero_asiento": numero_asiento,
        "id_comprobante_iva": id_comprobante_iva,
        "comprobante": {
            "id_comprobante_iva": id_comprobante_iva,
            "id_asiento": id_asiento,
            "numero_asiento": numero_asiento,
            "id_tipo_documento": id_tipo_documento,
            "id_tipo_iva": id_tipo_iva or None,
            "documento_codigo": documento_codigo,
            "fecha": fecha,
            "numero_comprobante": numero_comprobante,
            "comprobante": f"{documento_codigo}-{numero_comprobante}",
            "condicion": condicion,
            "ruc": ruc,
            "razon_social": razon_social,
            "id_cuenta": id_cuenta,
            "cuenta_codigo": request.form.get("cuenta_codigo", "").strip(),
            "cuenta_nombre": request.form.get("cuenta_nombre", "").strip(),
            "id_cta_iva_5": id_cta_iva_5,
            "cta_iva_5_codigo": request.form.get("cta_iva_5", "").strip() or request.form.get("cta_iva_5_codigo", "").strip(),
            "cta_iva_5_nombre": request.form.get("cta_iva_5_nombre", "").strip(),
            "id_cta_iva_10": id_cta_iva_10,
            "cta_iva_10_codigo": request.form.get("cta_iva_10", "").strip() or request.form.get("cta_iva_10_codigo", "").strip(),
            "cta_iva_10_nombre": request.form.get("cta_iva_10_nombre", "").strip(),
            "id_contracuenta": id_contracuenta,
            "contracuenta_codigo": request.form.get("contracuenta", "").strip() or request.form.get("contracuenta_codigo", "").strip(),
            "contracuenta_nombre": request.form.get("contracuenta_nombre", "").strip(),
            "detalle": detalle,
            "exento": str(exento),
            "gravado_5": str(gravado_5),
            "iva_5": str(iva_5),
            "gravado_10": str(gravado_10),
            "iva_10": str(iva_10),
            "total": str(total),
            "moneda": moneda,
            "tipo_cambio": str(tipo_cambio),
            "tipo_iva_denominacion": tipo_iva_denominacion
        }
    })

@app.route("/cliente/<int:id_cliente>/buscar-cuentas")
def buscar_cuentas(id_cliente):
    q = request.args.get("q", "").strip()

    if not q:
        return jsonify([])

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id_cuenta,
                    codigo,
                    denominacion
                FROM cuenta_contable
                WHERE id_cliente = %s
                  AND (
                        codigo ILIKE %s
                        OR denominacion ILIKE %s
                      )
                ORDER BY codigo
                LIMIT 20
            """, (id_cliente, f"{q}%", f"%{q}%"))

            rows = cur.fetchall()

    cuentas = [
        {
            "id_cuenta": r[0],
            "codigo": r[1],
            "nombre": r[2]
        }
        for r in rows
    ]

    return jsonify(cuentas)


@app.route("/buscar-personas-ref")
def buscar_personas_ref():
    q = request.args.get("q", "").strip()

    if not q:
        return jsonify([])

    q_num = "".join(ch for ch in q if ch.isdigit())

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    rf_numero,
                    COALESCE(rf_nombre, '') AS nombre_completo
                FROM personas_ref
                WHERE rf_numero ILIKE %s
                   OR REPLACE(rf_numero, '-', '') ILIKE %s
                ORDER BY rf_numero
                LIMIT 10
            """, (f"{q}%", f"{q_num}%"))
            rows = cur.fetchall()

    personas = [
        {
            "numero": r[0],
            "nombre": r[1] or ""
        }
        for r in rows
    ]

    return jsonify(personas)


if __name__ == "__main__":
    app.run(debug=True)
