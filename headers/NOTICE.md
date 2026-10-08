# Third-party reference headers

Redistributed **unmodified** so that `schema/verify_roundtrip.py` can be re-run by
anyone. These are not our code.

| File | Source | License |
|---|---|---|
| `SkyCraft/protocol/skycraft_protocol.h` | [chasmlol/SkyCraft](https://github.com/chasmlol/SkyCraft) | MIT |
| `FalloutCraft/skycraft_protocol.h` | [zeyvu/FalloutCraft](https://github.com/zeyvu/FalloutCraft) | MIT (derived from SkyCraft) |

---

## SkyCraft — LICENSE (MIT)

```
MIT License

Copyright (c) 2026 chasmlol

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## FalloutCraft — LICENSE (MIT, derived from SkyCraft)

```
MIT License

Copyright (c) 2026 chasmlol (SkyCraft)
Copyright (c) 2026 zeyvu (FalloutCraft)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

**Not included:** `ValCraft/protocol/valcraft_protocol.h`. That repository ships **no
LICENSE**, so it is read-only to this project and is not redistributed. To run that
line anyway, point `PT_HEADERS_DIR` at your own copy:

    PT_HEADERS_DIR=/path/to/dir python schema/verify_roundtrip.py
