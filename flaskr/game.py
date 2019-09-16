from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import list_tp_to_list_dict, tp_to_dict, get_conn_db
import random as rd


log_new_game = []
search_number = []
bp = Blueprint('game', __name__)


@bp.route("/")
def index():
    global log_new_game, search_number
    log_new_game = []
    search_number = pick_number()
    conn = get_conn_db()
    cur = conn.cursor()

    cur.execute('''
            SELECT game.id, author_id, username, game_begin, 
            conceived_number, count_step, time_game, win_los
            FROM game JOIN author ON game.author_id = author.id
            ORDER BY game_begin DESC;
            ''')

    game_cur = cur.fetchall()
    lst_bd = list_tp_to_list_dict(game_cur, cur)

    cur.close()
    conn.commit()
    conn.close()

    return render_template("blog/index.html", games=lst_bd)


def get_game_log(id_game):

    conn = get_conn_db()
    cur = conn.cursor()
    cur.execute(
            "SELECT log.id, game_id, log_game"
            " FROM log  JOIN game ON log.game_id = game.id"
            " WHERE game_id = %s",
            (id_game,),
        )
    cur_game = cur.fetchall()
    game_log = list_tp_to_list_dict(cur_game, cur)
    cur.close()
    conn.commit()
    conn.close()

    if game_log is None:
        abort(404, "Game id {0} doesn't exist.".format(id_game))
    return game_log


def validator_input_number(input_str=''):
    error_str = ''
    if input_str[0] != '0' and input_str.isdigit() and len(set(input_str)) == 4:
        return error_str, input_str
    else:
        error_str = 'Не корректный ввод! Допустимые значания 1234567890, четыре цифры, все разные, первая не 0'
        return error_str, input_str


def pick_number():
    search_number_lst = []
    list_select = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    step = 0
    while len(search_number_lst) <= 3:
        step += 1
        number = rd.choice(list_select)
        if number != '0' or step != 1:
            list_select.remove(number)
            search_number_lst.append(number)
    return search_number_lst


def check_number(user_input_str='', search_number_lst=[]):
    user_number_lst = list(user_input_str)
    print(search_number_lst)
    bulls = 0
    for i in range(len(user_number_lst)):
        if user_number_lst[i] == search_number_lst[i]:
            bulls += 1
    set_search = set(search_number_lst)
    set_user = set(user_number_lst)
    cows = len(set_search & set_user) - bulls
    answer = str(bulls) + str(cows)
    return answer


@bp.route("/new_game", methods=("GET", "POST"))
@login_required
def new_game():
    global log_new_game, search_number

    if request.method == "POST":
        step_game = request.form["step_game"]
        valid_input = validator_input_number(input_str=step_game)

        if valid_input[0] != '':
            flash(valid_input[0])
        else:
            last_step = valid_input[1]
            bulls_cows = check_number(user_input_str=last_step, search_number_lst=search_number)

            # conn = get_conn_db()
            # cur = conn.cursor()
            # cur.execute(
            #     "INSERT INTO log (game_id, game_log)"
            #     " VALUES (%s, %s)",
            #     (step_game, g.user["id"]),
            # )
            # cur.close()
            # conn.commit()
            # conn.close()

            step_dict = {'log_game': last_step + ' ' + bulls_cows}
            log_new_game.append(step_dict)
            return render_template("blog/new_game.html", steps=log_new_game, last_step=last_step,
                                   search_num=search_number, id_game=999)

    return render_template("blog/new_game.html", steps=log_new_game)


@bp.route("/<int:id_game>/view_game", methods=("GET", "POST"))
@login_required
def view_game(id_game):
    game_log = get_game_log(id_game)
    return render_template("blog/view_game.html", steps=game_log, id_game=id_game)


@bp.route("/rules")
def rules():
    return render_template("blog/rules.html")


@bp.route("/<int:id_game>/los", methods=("POST",))
@login_required
def los(id_game):
    global log_new_game
    str_flash = 'Игра номер ' + str(id_game) + ' -  сдача!'
    flash(str_flash)
    log_new_game = []

    # conn = get_conn_db()
    # cur = conn.cursor()
    # cur.execute(
    #     "DELETE FROM post WHERE id = %s", (id,)
    # )
    # cur.close()
    # conn.commit()
    # conn.close()
    return redirect(url_for("game.index"))
