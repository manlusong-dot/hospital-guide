const api = require('../../utils/api');
const req = require('../../utils/request');

Page({
  data: {
    patientName: '',
    records: []
  },

  onShow: function () {
    this.setData({ patientName: wx.getStorageSync('patientName') || '' });
    this.loadRecords();
  },

  onNameInput: function (e) {
    const name = e.detail.value;
    this.setData({ patientName: name });
    wx.setStorageSync('patientName', name);
    this.loadRecords();
  },

  loadRecords: function () {
    const self = this;
    const name = this.data.patientName.trim();
    api.registrations(name || null).then(function (list) {
      self.setData({ records: list });
    }).catch(function () {
      self.setData({ records: [] });
    });
  },

  goRegister: function () {
    wx.navigateTo({ url: '/pages/register/register' });
  },

  goJourney: function () {
    wx.navigateTo({ url: '/pages/journey/journey' });
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
  },

  goGuide: function () {
    wx.navigateTo({ url: '/pages/guide/guide' });
  }
});
