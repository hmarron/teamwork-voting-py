import mysql.connector
import logging

def main():
    global db

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="dev",
        database="polls"
    )

    clear()
    pollId = create_poll("who am i", 1, 2)
    add_choices(pollId, ["hugh", "jon", "joe"])
    remove_choice(pollId, 1)
    cast_vote(pollId, 1, 2)
    cast_vote(pollId, 1, 3)


def message_create_webhook():
    # listen for message created
    return

def post_message():
    # used for the following
    # current poll updates
    # help
    # user has voted
    return




######################
# User commands
######################
def create_poll(question, channelId, createdBy):
    cursor = db.cursor()

    # create poll
    sql = "INSERT INTO polls (question, channelId, createdBy) VALUES (%s, %s, %s)"
    val = (question, channelId, createdBy)

    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error(e)
        return

    return cursor.lastrowid


# If bad choice, log error and do nothing.
def cast_vote(pollId, userId, pollChoiceId):
    cursor = db.cursor()

    # get choice id from pollchoiceId
    sql = "SELECT id FROM choices WHERE pollId = %s AND pollChoiceId = %s"
    val = (pollId, pollChoiceId)
    try:
        cursor.execute(sql, val)
        choiceId = cursor.fetchone()[0]
    except Exception as e:
        logging.error(e)
        return

    # delete existing vote
    sql = "DELETE FROM votes WHERE pollId = %s AND userId = %s"
    val = (pollId, userId)
    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error(e)
        return

    # insert vote
    sql = "INSERT INTO votes (pollId, userId, choiceId) VALUES (%s, %s, %s)"
    val = (pollId, userId, choiceId)
    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error(e)
        return

    return

def add_choices(pollId, answers):
    cursor = db.cursor()
    for i in range(len(answers)):
        sql = "INSERT INTO choices (pollId, answer, pollChoiceId) VALUES (%s, %s, %s)"
        val = (pollId, answers[i], i+1)

        try:
            cursor.execute(sql, val)
            db.commit()
        except Exception as e:
            logging.error(e)
            return

def remove_choice(pollId, pollChoiceId):
    cursor = db.cursor()
    sql = "DELETE FROM choices WHERE pollId = %s AND pollChoiceId = %s"
    val = (pollId, pollChoiceId)

    try:
        cursor.execute(sql, val)
        db.commit()
    except Exception as e:
        logging.error(e)
        return

def clear():
    cursor = db.cursor()
    clear_commands = ["DELETE FROM votes", "DELETE FROM choices", "DELETE FROM polls"]
    for sql in clear_commands:
        try:
            cursor.execute(sql)
            db.commit()
        except Exception as e:
            logging.error(e)
            return

def help_text():
    return

if __name__ == "__main__":
    main()



# TODO max 50 chars on questions and answers
