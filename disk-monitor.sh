#!/bin/bash

# 创建日志目录
mkdir -p /var/log/disk-monitor

# 设置日志文件名
log_file="/var/log/disk-monitor/$(date +'%Y-%m-%d').log"

# 检查日志文件是否存在
if [ ! -f $log_file ]; then
  # 写入日志标题
  printf "%-20s %-10s %-10s %-10s\n" "时间" "rMB/s" "wMB/s" "%util" > $log_file
fi
# 设置每小时运行iostat命令的次数
x=180

while true; do
  # 运行iostat命令，获取磁盘信息
  disk_info=$(iostat -dxm /dev/dm-3 5 $x | grep 'dm-3')
  rmb_avg=$(echo "$disk_info" | awk '{sum+=$6} END {print sum/NR}')
  wmb_avg=$(echo "$disk_info" | awk '{sum+=$7} END {print sum/NR}')
  util_avg=$(echo "$disk_info" | awk '{sum+=$14} END {print sum/NR}')

  # 写入日志文件
  printf "%-20s %-10.2f %-10.2f %-10.2f\n" "$(date +'%H:%M:%S')" "$rmb_avg" "$wmb_avg" "$util_avg" >> $log_file

  # 每天计算一次总平均值，并写入日志文件
  if (( $(date +%s) > $(date -d "00:00" +%s) && $(date +%s) < $(date -d "00:30" +%s) ));then
    day_rmb_avg=$(awk 'NR>1 {sum+=$2} END {print sum/(NR-1)}' $log_file)
    day_wmb_avg=$(awk 'NR>1 {sum+=$3} END {print sum/(NR-1)}' $log_file)
    day_util_avg=$(awk 'NR>1 {sum+=$4} END {print sum/(NR-1)}' $log_file)

   # printf "\n%-20s %-10.2f %-10.2f %-10.2f\n" "average:" "$day_rmb_avg" "$day_wmb_avg" "$day_util_avg" >> $log_file

    # 设置新的日志文件名
    log_file="/var/log/disk-monitor/$(date +'%Y-%m-%d').log"

     # 检查新的日志文件是否存在
    if [ ! -f $log_file ]; then
      # 写入新的日志标题
      printf "%-20s %-10s %-10s %-10s\n" "时间" "rMB/s" "wMB/s" "%util" > $log_file
    fi
  fi

  # 删除超过一个月的日志文件
  find /var/log/disk-monitor -mtime +200 -type f -delete
done

