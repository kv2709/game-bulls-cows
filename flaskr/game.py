from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import list_tp_to_list_dict, tp_to_dict, get_conn_db
import random as rd
import datetime

log_new_game = []
lst_new_game = []
search_number = []
time_game = []
bp = Blueprint('game', __name__)


@bp.route("/")
def index():
    global log_new_game, search_number, time_game, lst_new_game
    log_new_game = []
    lst_new_game = []
    search_number = []
    time_game = []
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
    step = 1
    while len(search_number_lst) <= 3:
        number = rd.choice(list_select)
        if number != '0' or step != 1:
            step += 1
            list_select.remove(number)
            search_number_lst.append(number)
    return search_number_lst


def check_number(user_input_str='', search_number_lst=[]):
    user_number_lst = list(user_input_str)
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
    global log_new_game, search_number, time_game, lst_new_game

    time_session_game = datetime.datetime.now()
    time_game.append(time_session_game)

    if request.method == "POST":
        step_game = request.form["step_game"]
        valid_input = validator_input_number(input_str=step_game)

        if valid_input[0] != '':
            flash(valid_input[0])
        else:
            if not search_number:
                error = 'Слишком долгое ожидание! Игра завершена без сохраннеия!'
                flash(error)
                return redirect(url_for("game.index"))

            last_step = valid_input[1]
            bulls_cows = check_number(user_input_str=last_step, search_number_lst=search_number)
            step_dict = {'log_game': last_step + ' ' + bulls_cows}
            log_new_game.append(step_dict)
            lst_new_game.append(last_step + ' ' + bulls_cows)
            if bulls_cows == '40':
                count_record_time = len(time_game)
                sum_time_game = time_game[count_record_time - 1] - time_game[0]
                sum_time_game_sec = sum_time_game.total_seconds()
                # Запись сесии игры ====================================
                conn = get_conn_db()
                cur = conn.cursor()
                search_number_str = ''.join(search_number)
                count_step = len(log_new_game)
                cur.execute("INSERT INTO game (author_id, conceived_number, count_step, time_game, win_los)"
                            "VALUES (%s, %s, %s, %s,%s)",
                            (g.user["id"], search_number_str, count_step, sum_time_game_sec, 1)
                            )
                cur.execute("SELECT * FROM game ORDER BY id DESC LIMIT 1")
                game_id = cur.fetchone()[0]

                for i in range(len(lst_new_game)):
                    cur.execute("INSERT INTO log (game_id, log_game)"
                                " VALUES (%s, %s)",
                                (game_id, lst_new_game[i]),
                                )

                cur.close()
                conn.commit()
                conn.close()

                message_win = 'Поздравляю с победой! Количество ходов в сесии ' + str(count_step)
                flash(message_win)
                return redirect(url_for("game.index"))

            return render_template("blog/new_game.html", steps=log_new_game, last_step=last_step,
                                   search_num=search_number)

    return render_template("blog/new_game.html")


@bp.route("/<int:id_game>/view_game", methods=("GET", "POST"))
@login_required
def view_game(id_game):
    game_log = get_game_log(id_game)
    return render_template("blog/view_game.html", steps=game_log)


@bp.route("/rules")
def rules():
    return render_template("blog/rules.html")

#
# @bp.route("/<int:id_game>/los", methods=("POST",))
# @login_required
# def los(id_game):


@bp.route("/los", methods=("POST",))
@login_required
def los():
    global log_new_game
    str_flash = 'Вы сдались! Запись сеанса игры не произведена!'
    flash(str_flash)
    return redirect(url_for("game.index"))


@bp.route("/init_game")
@login_required
def init_game():
    global log_new_game, search_number, time_game, lst_new_game
    log_new_game = []
    lst_new_game = []
    search_number = []
    time_game = []
    search_number = pick_number()
    str_flash = 'Число загадано! Можно запускать новую игру!'
    flash(str_flash)
    return redirect(url_for("game.index"))
