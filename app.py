import os
import sqlite3
from contextlib import closing
from typing import List, Optional

from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    url_for,
    flash,
)

DATABASE_NAME = "students.db"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change_me_for_real_project"
    app.config["DATABASE"] = os.path.join(app.root_path, DATABASE_NAME)

    # ---------- Работа с БД ---------- #

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            db_path = app.config["DATABASE"]
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(exception: Optional[BaseException]) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db() -> None:
    # таблицса если нет
        db = get_db()
        create_sql = """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            group_name TEXT NOT NULL,
            age INTEGER NOT NULL
        );
        """
        with closing(db.cursor()) as cursor:
            cursor.execute(create_sql)
            db.commit()

    with app.app_context():
        init_db()

    @app.route("/")
    def index() -> str:
        return redirect(url_for("students_list"))

    @app.route("/students")
    def students_list() -> str:
# вывод списка студентов
        db = get_db()
        with closing(db.cursor()) as cursor:
            cursor.execute(
                "SELECT id, full_name, group_name, age FROM students ORDER BY id;"
            )
            rows: List[sqlite3.Row] = cursor.fetchall()

        return render_template("students_list.html", students=rows)

    @app.route("/students/add", methods=["GET", "POST"])
    def student_add() -> str:
    # создание
        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            group_name = request.form.get("group_name", "").strip()
            age_raw = request.form.get("age", "").strip()

            if not full_name or not group_name or not age_raw:
                flash("Заполните, пожалуйста, все поля.", "danger")
                return render_template("student_form.html", mode="add")

            try:
                age = int(age_raw)
            except ValueError:
                flash("Возраст должен быть целым числом.", "danger")
                return render_template("student_form.html", mode="add")

            db = get_db()
            with closing(db.cursor()) as cursor:
                cursor.execute(
                    """
                    INSERT INTO students (full_name, group_name, age)
                    VALUES (?, ?, ?);
                    """,
                    (full_name, group_name, age),
                )
                db.commit()

            flash("Студент добавлен.", "success")
            return redirect(url_for("students_list"))

        return render_template("student_form.html", mode="add")

    @app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
    def student_edit(student_id: int) -> str:
    # обновление
        db = get_db()
        with closing(db.cursor()) as cursor:
            cursor.execute(
                "SELECT id, full_name, group_name, age FROM students WHERE id = ?;",
                (student_id,),
            )
            row: Optional[sqlite3.Row] = cursor.fetchone()

        if row is None:
            flash("Студент не найден.", "warning")
            return redirect(url_for("students_list"))

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            group_name = request.form.get("group_name", "").strip()
            age_raw = request.form.get("age", "").strip()

            if not full_name or not group_name or not age_raw:
                flash("Заполните, пожалуйста, все поля.", "danger")
                return render_template("student_form.html", mode="edit", student=row)

            try:
                age = int(age_raw)
            except ValueError:
                flash("Возраст должен быть целым числом.", "danger")
                return render_template("student_form.html", mode="edit", student=row)

            db = get_db()
            with closing(db.cursor()) as cursor:
                cursor.execute(
                    """
                    UPDATE students
                    SET full_name = ?, group_name = ?, age = ?
                    WHERE id = ?;
                    """,
                    (full_name, group_name, age, student_id),
                )
                db.commit()

            flash("Данные студента обновлены.", "success")
            return redirect(url_for("students_list"))

        return render_template("student_form.html", mode="edit", student=row)

    @app.route("/students/<int:student_id>/delete", methods=["POST"])
    def student_delete(student_id: int) -> str:
    # удаление
        db = get_db()
        with closing(db.cursor()) as cursor:
            cursor.execute("DELETE FROM students WHERE id = ?;", (student_id,))
            db.commit()

        flash("Студент удалён.", "info")
        return redirect(url_for("students_list"))

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
