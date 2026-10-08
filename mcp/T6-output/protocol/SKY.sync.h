// Passthrough seqlock + SPSC ring skeletons (generated; companion to the header).
// These are ABI-neutral helpers: they only read/write the container offsets.
#pragma once
namespace skycraft::proto {

// seqlock: read a struct guarded by a u32 seq at `seq_off`.
template <typename T>
bool SeqlockRead(const std::uint8_t* base, std::uint64_t seq_off, T& out) {
  for (;;) {
    std::uint32_t s0 = *reinterpret_cast<const std::uint32_t*>(base + seq_off);
    if (s0 & 1u) { return false; }            // writer mid-update
    std::atomic_thread_fence(std::memory_order_acquire);
    std::memcpy(&out, base + seq_off + 8, sizeof(T));
    std::atomic_thread_fence(std::memory_order_acquire);
    std::uint32_t s1 = *reinterpret_cast<const std::uint32_t*>(base + seq_off);
    if (s0 == s1) { return true; }            // even, stable
  }
}

template <typename T>
void SeqlockWrite(std::uint8_t* base, std::uint64_t seq_off, const T& in) {
  auto* s = reinterpret_cast<std::uint32_t*>(base + seq_off);
  std::uint32_t s0 = *s + 1;                  // -> odd
  std::atomic_thread_fence(std::memory_order_release);
  *s = s0;
  std::atomic_thread_fence(std::memory_order_release);
  std::memcpy(base + seq_off + 8, &in, sizeof(T));
  std::atomic_thread_fence(std::memory_order_release);
  *s = s0 + 1;                                // -> even
}

// SPSC ring (power-of-two). head/tail are u64 at head_off/tail_off; data at data_off.
inline std::uint64_t RingMask(std::uint64_t data_bytes) { return data_bytes - 1; }
inline bool RingTryProduce(std::uint8_t* base, std::uint64_t head_off,
                           std::uint64_t data_off, std::uint64_t data_bytes,
                           const void* payload, std::uint64_t n) {
  std::uint64_t head = *reinterpret_cast<std::uint64_t*>(base + head_off);
  std::uint64_t mask = data_bytes - 1;
  if ((head & mask) + n > data_bytes) { return false; }  // no room (simple bound)
  std::uint64_t pos = head & mask;
  std::memcpy(base + data_off + pos, payload, n);
  *reinterpret_cast<std::uint64_t*>(base + head_off) = head + n;
  return true;
}
inline bool RingTryConsume(std::uint8_t* base, std::uint64_t tail_off,
                           std::uint64_t data_off, std::uint64_t data_bytes,
                           void* out, std::uint64_t n) {
  std::uint64_t tail = *reinterpret_cast<std::uint64_t*>(base + tail_off);
  std::uint64_t head = *reinterpret_cast<std::uint64_t*>(base + tail_off - 0x40);
  if (tail + n > head) { return false; }
  std::uint64_t mask = data_bytes - 1;
  std::uint64_t pos = tail & mask;
  std::memcpy(out, base + data_off + pos, n);
  *reinterpret_cast<std::uint64_t*>(base + tail_off) = tail + n;
  return true;
}
}  // namespace
