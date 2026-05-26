import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRoomStore = defineStore('room', () => {
  const roomCode = ref(null)
  const roomName = ref(null)
  const seats = ref([])

  function setRoom(code, name) {
    roomCode.value = code
    roomName.value = name
  }

  function setSeats(seatList) {
    seats.value = seatList
  }

  function updateSeat(seatId, status, userId, userName) {
    const seat = seats.value.find(s => s.id === seatId)
    if (seat) {
      seat.status = status
      seat.user_id = userId
      seat.user_name = userName
    }
  }

  return { roomCode, roomName, seats, setRoom, setSeats, updateSeat }
})
