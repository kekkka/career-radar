"""Owner-facing Telegram command interface."""
from radar_quality import daily_message

def command_keyboard():
    return {'keyboard':[[{'text':'/start'},{'text':'/status'}]],'resize_keyboard':True,'is_persistent':True}

def command_reply(command, history, avito=None):
    if command=='/start':
        return ('Солнышко, запускаю внеплановый поиск по всем 6 работодателям! 💗\n'
                'Пришлю новые подходящие вакансии и итоговый отчёт. Уже отправленные вакансии не дублирую.')
    if command=='/status':
        d=dict(history.get('diagnostics',{}))
        d.setdefault('day','ещё не сформирован')
        for key in ('runs','sent','duplicates','retries'): d.setdefault(key,0)
        if avito: d['avito']=avito
        if d['day']=='ещё не сформирован':
            return 'Career Radar 💗\nПоследний отчёт: ещё не сформирован.\nМониторинг настроен каждые 30 минут.'
        return daily_message(d)+'\n\nМониторинг настроен каждые 30 минут.'
    return ('Career Radar 💗\n/start — внеплановый поиск.\n/status — единый отчёт.\n'
            'Команды обрабатываются при ближайшей проверке Telegram.')
