const api = require('../../utils/api');
const req = require('../../utils/request');

function buildDates() {
  const dates = [];
  const now = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now.getTime() + i * 86400000);
    const text = (d.getMonth() + 1) + '月' + d.getDate() + '日';
    dates.push({ label: (i === 0 ? '今天 ' : '') + text, value: d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()), isToday: i === 0 });
  }
  return dates;
}

function pad(n) {
  return n < 10 ? '0' + n : '' + n;
}

function getDefaultSlotIndex() {
  const hour = new Date().getHours();
  if (hour < 12) return 0;
  if (hour < 17) return 1;
  return 2;
}

function getAvailableSlots(isToday) {
  const allSlots = ['上午', '下午', '晚上'];
  if (!isToday) return allSlots;
  const hour = new Date().getHours();
  if (hour < 12) return allSlots;
  if (hour < 17) return ['下午', '晚上'];
  return ['晚上'];
}

Page({
  data: {
    deptList: [],
    deptIndex: 0,
    doctorList: [],
    doctorIndex: -1,
    dates: [],
    dateIndex: 0,
    slots: ['上午', '下午', '晚上'],
    slotIndex: 0,
    patientName: '',
    result: null,
    records: []
  },

  onLoad: function () {
    const self = this;
    const dates = buildDates();
    const isToday = dates[0].isToday;
    const availableSlots = getAvailableSlots(isToday);
    const defaultSlotIndex = getDefaultSlotIndex();
    const adjustedSlotIndex = availableSlots.length <= defaultSlotIndex ? availableSlots.length - 1 : defaultSlotIndex;

    this.setData({
      dates: dates,
      slots: availableSlots,
      slotIndex: adjustedSlotIndex,
      patientName: wx.getStorageSync('patientName') || ''
    });
    api.departments().then(function (list) {
      const clinic = list.filter(function (d) {
        return d.category === '门诊' || d.category === '急诊';
      });
      self.setData({ deptList: clinic });
      if (clinic.length > 0) self.loadDoctors(clinic[0].id);
    }).catch(function (err) {
      req.showError(err);
    });
    this.loadRecords();
  },

  onDeptChange: function (e) {
    const index = Number(e.detail.value);
    this.setData({ deptIndex: index, doctorIndex: -1, result: null });
    this.loadDoctors(this.data.deptList[index].id);
  },

  loadDoctors: function (deptId) {
    const self = this;
    api.doctors(deptId).then(function (list) {
      self.setData({ doctorList: list });
    }).catch(function (err) {
      req.showError(err);
    });
  },

  pickDoctor: function (e) {
    this.setData({ doctorIndex: Number(e.currentTarget.dataset.index), result: null });
  },

  onDateChange: function (e) {
    const index = Number(e.detail.value);
    const isToday = this.data.dates[index].isToday;
    const availableSlots = getAvailableSlots(isToday);
    this.setData({
      dateIndex: index,
      slots: availableSlots,
      slotIndex: 0
    });
  },

  onSlotChange: function (e) {
    this.setData({ slotIndex: Number(e.detail.value) });
  },

  onNameInput: function (e) {
    this.setData({ patientName: e.detail.value });
  },

  submit: function () {
    const self = this;
    const name = this.data.patientName.trim();
    if (!name) {
      wx.showToast({ title: '请填写就诊人姓名', icon: 'none' });
      return;
    }
    if (this.data.doctorIndex < 0) {
      wx.showToast({ title: '请先选择医生', icon: 'none' });
      return;
    }
    const date = this.data.dates[this.data.dateIndex];
    const slot = this.data.slots[this.data.slotIndex];
    // 检查今天已过时段
    if (date.isToday) {
      const hour = new Date().getHours();
      if (slot === '上午' && hour >= 12) {
        wx.showToast({ title: '今天上午已过，无法预约', icon: 'none' });
        return;
      }
      if (slot === '下午' && hour >= 17) {
        wx.showToast({ title: '今天下午已过，无法预约', icon: 'none' });
        return;
      }
    }
    wx.setStorageSync('patientName', name);
    const doctor = this.data.doctorList[this.data.doctorIndex];
    api.register(name, doctor.id, date.value, slot).then(function (res) {
      wx.showToast({ title: '挂号成功', icon: 'success', duration: 2000 });
      self.setData({ result: res });
      self.loadRecords();
      setTimeout(function () {
        wx.switchTab({ url: '/pages/my/my' });
      }, 700);
    }).catch(function (err) {
      req.showError(err);
    });
  },

  loadRecords: function () {
    const self = this;
    const name = this.data.patientName ? this.data.patientName.trim() : '';
    api.registrations(name || null).then(function (list) {
      self.setData({ records: list });
    }).catch(function () {
      self.setData({ records: [] });
    });
  },

  enterJourney: function (e) {
    const record = this.data.records[Number(e.currentTarget.dataset.index)];
    if (!record || !record.dept_id) {
      wx.showToast({ title: '预约科室信息不完整', icon: 'none' });
      return;
    }
    if (record.can_enter === false && !record.journey_completed) {
      wx.showToast({ title: '预约时间段已过，不能进入流程', icon: 'none' });
      return;
    }
    const startKey = record.journey_completed ? null : 'checkin';
    api.journeySession(null, record.dept_id, startKey, record.id).then(function (res) {
      getApp().globalData.sessionId = res.session_id;
      getApp().globalData.currentDept = {
        id: record.dept_id,
        name: record.dept_name,
        floor: record.floor
      };
      wx.navigateTo({
        url: '/pages/journey/journey?session=' + encodeURIComponent(res.session_id) +
          '&dept=' + encodeURIComponent(record.dept_id)
      });
    }).catch(function (err) {
      req.showError(err);
    });
  }
});
