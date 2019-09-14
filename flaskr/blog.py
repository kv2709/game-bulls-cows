from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import list_tp_to_list_dict, tp_to_dict, get_conn_db


bp = Blueprint('blog', __name__)


@bp.route("/")
def index():
    conn = get_conn_db()
    cur = conn.cursor()

    cur.execute('''
            SELECT post.id, title, body, created, author_id, username
            FROM post JOIN author ON post.author_id = author.id
            ORDER BY created DESC;
            ''')

    post_cur = cur.fetchall()
    lst_bd = list_tp_to_list_dict(post_cur, cur)

    cur.close()
    conn.commit()
    conn.close()
    return render_template("blog/index.html", posts=lst_bd)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    conn = get_conn_db()
    cur = conn.cursor()
    cur.execute(
            "SELECT post.id, title, body, created, author_id, username"
            " FROM post  JOIN author ON post.author_id = author.id"
            " WHERE post.id = %s",
            (id,),
        )
    cur_post = cur.fetchone()
    post = tp_to_dict(cur_post, cur)
    cur.close()
    conn.commit()
    conn.close()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))
    if check_author and post["author_id"] != g.user["id"]:
        abort(403)
    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            conn = get_conn_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO post (title, body, author_id)" " VALUES (%s, %s, %s)",
                (title, body, g.user["id"]),
            )
            cur.close()
            conn.commit()
            conn.close()

            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            conn = get_conn_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE post SET title = %s, body = %s WHERE id = %s", (title, body, id)
            )
            cur.close()
            conn.commit()
            conn.close()

            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    conn = get_conn_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM post WHERE id = %s", (id,)
    )
    cur.close()
    conn.commit()
    conn.close()
    return redirect(url_for("blog.index"))
