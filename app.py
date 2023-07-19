from flask import Flask, render_template, request
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    today = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        date = request.form['date'] or today
        category = request.form['category'] or 'dump'
        action = request.form.get('action')
        if action == '5days':
            img = get_disk_usage_plot_5days(category)
        else:
            img = get_disk_usage_plot(date, category)
        return render_template('index.html', date=date, category=category, img=img, today=today)
    return render_template('index.html', today=today, category='dump')

def get_disk_usage_plot(date, category):
    log_dir = f'/var/log/disk-monitor/{category}'
    log_file = os.path.join(log_dir, f'{date}.log')
     # Check if the log file exists
    if not os.path.exists(log_file):
        return f'没有找到 {date} 的日志文件'

    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    times = []
    rMBs = []
    wMBs = []
    utils = []
    for line in lines:
        data = line.split()
        if len(data) < 4:
            # Invalid line, skip it
            continue
        try:
            time = data[0]
            time = datetime.strptime(time, '%H:%M:%S')
            rMB = float(data[1])
            wMB = float(data[2])
            util = float(data[3])
        except ValueError:
            # Invalid data, skip it
            continue
        times.append(time)
        rMBs.append(rMB)
        wMBs.append(wMB)
        utils.append(util)

    times = mdates.date2num(times)

    fig, axs = plt.subplots(3, 1, figsize=(15, 15))
    plt.subplots_adjust(hspace=0.5)

    axs[0].plot(times, rMBs)
    axs[0].set_xlabel('Time')
    axs[0].set_ylabel('rMB/s')
    axs[0].set_title(f'rMB/s on {date}')
    axs[0].text(0.5, 0.9, 'Read I/O speed', transform=axs[0].transAxes)

    axs[1].plot(times, wMBs)
    axs[1].set_xlabel('Time')
    axs[1].set_ylabel('wMB/s')
    axs[1].set_title(f'wMB/s on {date}')
    axs[1].text(0.5, 0.9, 'Write I/O speed', transform=axs[1].transAxes)

    axs[2].plot(times, utils)
    axs[2].set_xlabel('Time')
    axs[2].set_ylabel('%util')
    axs[2].set_title(f'%util on {date}')
    axs[2].text(0.5, 0.9, 'Disk I/O %usage', transform=axs[2].transAxes)

    for ax in axs:
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.tick_params(axis='x', rotation=45)

    img = BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def get_disk_usage_plot_5days(category):
    log_dir = f'/var/log/disk-monitor/{category}'

    # Calculate the dates of the past 5 days
    dates = [(datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(4, -1, -1)]

    times = []
    rMBs = []
    wMBs = []
    utils = []
    for date in dates:
        log_file = os.path.join(log_dir, f'{date}.log')
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            data = line.split()
            if len(data) < 4:
                # Invalid line, skip it
                continue
            try:
                time = data[0]
                rMB = float(data[1])
                wMB = float(data[2])
                util = float(data[3])
            except ValueError:
                # Invalid data, skip it
                continue
            times.append(f'{date} {time}')
            rMBs.append(rMB)
            wMBs.append(wMB)
            utils.append(util)

    fig, axs = plt.subplots(3, 1, figsize=(20, 15))
    plt.subplots_adjust(hspace=0.5)

    axs[0].plot(times, rMBs, color='red')
    axs[1].plot(times, wMBs, color='red')
    axs[2].plot(times, utils, color='red')

    axs[0].set_xlabel('Time')
    axs[0].set_ylabel('rMB/s')
    axs[0].set_title(f'rMB/s in the past 5 days')

    axs[1].set_xlabel('Time')
    axs[1].set_ylabel('wMB/s')
    axs[1].set_title(f'wMB/s in the past 5 days')

    axs[2].set_xlabel('Time')
    axs[2].set_ylabel('%util')
    axs[2].set_title(f'%util in the past 5 days')

    xticks = []
    xticklabels = []
    for i in range(0, len(times), 1):
        if i % (24 * 12) == 0 or i % (1 * 12) == 0:
            xticks.append(i)
            xticklabels.append(times[i][11:])
        elif i % (24 * 12) == 0:
            xticks.append(i)
            xticklabels.append('')
    for ax in axs:
        ax.set_xticks([0] + xticks + [len(times) - 1])
        ax.set_xticklabels([dates[0]] + xticklabels + [dates[-1]], rotation=45)

    img = BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()


if __name__ == '__main__':
    app.run()

