using System;
using System.Runtime.InteropServices;
namespace skycraft.proto
{
    public static class Sync
    {
        // seqlock read over a pinned byte[] base at byte offset seqOff.
        public static bool SeqlockRead(byte[] buf, int seqOff)
        {
            int s0 = BitConverter.ToInt32(buf, seqOff);
            if ((s0 & 1) != 0) return false;
            int s1 = BitConverter.ToInt32(buf, seqOff);
            return s0 == s1;
        }
        public static void RingProduce(byte[] buf, int headOff, int dataOff, int dataBytes, byte[] payload)
        {
            long head = BitConverter.ToInt64(buf, headOff);
            int pos = (int)(head & (dataBytes - 1));
            Array.Copy(payload, 0, buf, dataOff + pos, payload.Length);
            head += payload.Length;
            Array.Copy(BitConverter.GetBytes(head), 0, buf, headOff, 8);
        }
    }
}
