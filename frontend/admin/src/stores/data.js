import { defineStore } from 'pinia'
import {
  SEED_DEPARTMENTS,
  SEED_EXAM_PREP,
  SEED_MEDICINE_GUIDE,
  SEED_DOCTORS,
} from '@/data/seed'

const DEFAULT_USERS = [
  { id: 'admin', username: 'admin', password: 'admin123', name: '系统管理员', role: '超级管理员', status: '启用', createdAt: '2025-01-01' },
]

const NS = 'hospital-admin-data'

function load(key, seed) {
  try {
    const raw = localStorage.getItem(`${NS}:${key}`)
    if (raw) return JSON.parse(raw)
  } catch (e) {
    /* 忽略损坏数据，回退种子 */
  }
  return seed
}

function save(key, value) {
  localStorage.setItem(`${NS}:${key}`, JSON.stringify(value))
}

function newId(prefix) {
  return `${prefix}${Date.now().toString(36)}`
}

export const useDataStore = defineStore('data', {
  state: () => ({
    departments: load('departments', SEED_DEPARTMENTS),
    examPrep: load('examPrep', SEED_EXAM_PREP),
    medicineGuide: load('medicineGuide', SEED_MEDICINE_GUIDE),
    doctors: load('doctors', SEED_DOCTORS),
    users: load('users', DEFAULT_USERS),
  }),
  actions: {
    // 科室
    addDepartment(row) {
      const item = { ...row, id: row.id || newId('d') }
      this.departments.push(item)
      save('departments', this.departments)
      return item
    },
    updateDepartment(row) {
      const i = this.departments.findIndex((d) => d.id === row.id)
      if (i >= 0) {
        this.departments[i] = { ...row }
        save('departments', this.departments)
      }
    },
    removeDepartment(id) {
      this.departments = this.departments.filter((d) => d.id !== id)
      save('departments', this.departments)
    },
    // 检查须知
    addExam(row) {
      const item = { ...row, id: row.id || newId('ex') }
      this.examPrep.push(item)
      save('examPrep', this.examPrep)
      return item
    },
    updateExam(row) {
      const i = this.examPrep.findIndex((d) => d.id === row.id)
      if (i >= 0) {
        this.examPrep[i] = { ...row }
        save('examPrep', this.examPrep)
      }
    },
    removeExam(id) {
      this.examPrep = this.examPrep.filter((d) => d.id !== id)
      save('examPrep', this.examPrep)
    },
    // 用药常识
    addMedicine(row) {
      const item = { ...row, id: row.id || newId('med') }
      this.medicineGuide.push(item)
      save('medicineGuide', this.medicineGuide)
      return item
    },
    updateMedicine(row) {
      const i = this.medicineGuide.findIndex((d) => d.id === row.id)
      if (i >= 0) {
        this.medicineGuide[i] = { ...row }
        save('medicineGuide', this.medicineGuide)
      }
    },
    removeMedicine(id) {
      this.medicineGuide = this.medicineGuide.filter((d) => d.id !== id)
      save('medicineGuide', this.medicineGuide)
    },
    // 医生
    addDoctor(row) {
      const item = { ...row, id: row.id || newId('doc') }
      this.doctors.push(item)
      save('doctors', this.doctors)
      return item
    },
    updateDoctor(row) {
      const i = this.doctors.findIndex((d) => d.id === row.id)
      if (i >= 0) {
        this.doctors[i] = { ...row }
        save('doctors', this.doctors)
      }
    },
    removeDoctor(id) {
      this.doctors = this.doctors.filter((d) => d.id !== id)
      save('doctors', this.doctors)
    },
    // 用户
    addUser(row) {
      const item = { ...row, id: row.id || row.username }
      this.users.push(item)
      save('users', this.users)
      return item
    },
    updateUser(row) {
      const i = this.users.findIndex((u) => u.id === row.id)
      if (i >= 0) {
        this.users[i] = { ...row }
        save('users', this.users)
      }
    },
    removeUser(id) {
      this.users = this.users.filter((u) => u.id !== id)
      save('users', this.users)
    },
  },
})
