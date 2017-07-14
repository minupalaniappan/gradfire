from ...utils.db_utils import conn
import psycopg2
def getPrograms():
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT programs.id,
        programs.name,
        variant,
        program_types.name "type",
        (programs.name || ' '
            || initcap(program_types.name)
            || coalesce(' - ' || variant, '')) long_name -- Hides dash if variant is null
        FROM programs
        JOIN program_types ON program_types.id = programs.program_type_id""")
    return cur.fetchall()

