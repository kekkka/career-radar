"""Owner-facing Telegram replies; no secrets or private vacancy content."""
def command_reply(command, history):
    if command == '/status':
        d=history.get('diagnostics',{})
        return ('Career Radar 💗\n'
                'Мониторинг настроен каждые 30 минут.\n'
                'Последний отчёт: '+str(d.get('day','ещё не сформирован'))+'\n'
                'Отправлено за день: '+str(d.get('sent',0))+'\n'
                'Команды проверяются отдельно от поиска; GitHub может задерживать запуск.')
    return ('Солнышко, Career Radar на связи! 💗\n'
            'Ищу актуальные вакансии Product Manager и Product Analyst с обязательным опытом до 2 лет.\n'
            'Мониторинг настроен каждые 30 минут. Если подходящих вакансий нет, сообщений о вакансиях не будет.\n'
            '/status — последний отчёт.\n'
            'Команды проверяются отдельно от поиска; мгновенный ответ не гарантируется.')
