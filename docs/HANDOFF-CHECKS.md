# Kiểm tra trước khi bàn giao · v4.1.1

Các lệnh dưới đây bổ sung kiểm tra kỹ thuật cho gói **baked VFX** xuất từ Studio
v4.1/v4.1.1. Bộ skill, adapter, định dạng nguồn và ba cổng nghiệm thu được giữ nguyên.
Không tự sửa ảnh, ghi vào `.studio`, đổi revision hoặc duyệt mỹ thuật/runtime.

## 1. Kiểm tra máy chạy

```sh
npm run doctor
```

Báo phiên bản Node, Python, Pillow và thử tạo PNG bằng native canvas. Node 22+
chạy editor/local CLI; Node 22.13+ chạy bộ kiểm tra engine. Thiếu canvas không chặn
editor/browser: cài bằng `npm install` nếu cần render CLI hoặc kiểm pixel. Python
3.10+/Pillow dùng cho bộ QA sprite. `STUDIO_PYTHON` chọn Python cho doctor/art/skill
CLI; các ví dụ `python3` bên dưới cần thay bằng executable Python trên máy nếu khác.
Doctor không cài gì, không khởi động server và không xác nhận engine đã chạy.

## 2. Xuất và kiểm tra VFX

```sh
npm run production -- vfx projects/combat-vfx.rig.json --clip attack_se --fps 24 --engine all --out candidate-vfx
npm run verify:pack -- candidate-vfx --out candidate-check.json
npm run verify:pack -- candidate-vfx --rerender --out candidate-deep-check.json
```

Report phải ở **ngoài** thư mục đang kiểm tra và tên output phải mới. Có thể bỏ
`--out` để đọc JSON trên stdout. Exit code 0 khi kiểm tra kỹ thuật qua, 1 khi lỗi.
Không thực thi code từ thư mục export; adapter được đọc như dữ liệu và đối chiếu
với nguồn tin cậy đi kèm Studio.

| Chế độ | Kiểm tra | Phụ thuộc |
| --- | --- | --- |
| Mặc định | File, PNG chunk/CRC/IHDR, kích thước/vùng atlas, timing, contract, nguồn/track/origin/events, adapter, SHA-256 | Node |
| `--pixels` | Thêm giải mã và so RGBA của mọi frame với ô atlas; cờ empty | Native canvas |
| `--rerender` | Bao gồm pixels; render lại từ source và so manifest + mọi PNG | Native canvas |

Mặc định **không giải mã PNG**, do đó CRC đúng không chứng minh luồng nén hay nội dung
pixel đúng; dùng `--pixels` hoặc `--rerender` cho kiểm tra sâu. So pixel dùng RGBA
hiển thị qua native canvas; không khẳng định giữ RGB ẩn dưới alpha 0. SHA-256 ghi
nhận chính xác bytes PNG/JSON/adapter. Render lại dùng cùng implementation trong
Studio nên là kiểm tra tính nhất quán nguồn–gói, không phải engine độc lập.

Gói cần có `vfx.json`, `source.rig.json`, `engine-pack.json`, các PNG, contract và
adapter nguyên bản từ exporter. Nếu dự án đã sửa adapter/material/metadata, kiểm
tra candidate gốc trước và lưu bản tích hợp ở thư mục khác. Công cụ không nhập
sprite/body pack hoặc gói custom từ engine khác.

## 3. Giới hạn texture và phát hiện thay đổi

```sh
npm run verify:pack -- candidate-vfx --pixels --max-texture-size 2048 --max-texture-mib 64 --out budget-check.json
npm run verify:pack -- candidate-vfx --baseline candidate-deep-check.json --out repeat-check.json
```

Các con số trên là **ví dụ do dự án chọn**, không phải giới hạn chung của mọi GPU.
Report đếm PNG atlas, số frame/track, bytes file, chiều texture lớn nhất và tổng
`width × height × 4` của atlas, kể cả trang không được tham chiếu sau khi trim
đầu/cuối clip. Đây là ước lượng RGBA không nén một bản texture, chưa tính bản sao
CPU/GPU, alignment, mipmap, compression hay nhiều instance. Trang atlas không dùng
được báo warning; không tự xóa khỏi candidate.

Baseline phát hiện đổi/thêm/xóa bytes kể từ report thành công trước. Để baseline
bên ngoài pack và giữ cùng bản đã duyệt. SHA-256 không phải chữ ký xác thực và không
thay thế review. Nếu thay ảnh/source, tạo report mới sau khi kiểm tra lại. Công cụ
không khóa thư mục; không chỉnh pack trong lúc kiểm tra.

Giới hạn kiểm tra: 64 MB/file, 512 MB/gói, 10.000 file/frame, 128 track, 64 triệu
pixel/PNG và 128 triệu pixel PNG cộng dồn. Không theo symlink và không đọc đường dẫn
thoát thư mục. Gói lớn hơn cần chia clip/giảm FPS/canvas.

## 4. Kiểm tra và tạo ZIP tool

```sh
python3 scripts/verify_release.py PATH_TO_NEW_TOOL.zip
python3 scripts/package-release.py ../NEW_TOOL.zip
```

Verifier kiểm đường dẫn, inventory, mọi SHA-256, version và danh tính cây nguồn;
không giải nén hay chạy code trong ZIP. Chỉ áp dụng ZIP tool từ v4.1.1, vì các bản
cũ chưa có checksum cho `release.json` và hash cây nguồn.

Đóng gói chạy được cả khi giải nén từ ZIP, chưa `git init`. Nếu có checkout đúng gốc,
metadata ghi commit và trạng thái dirty; nếu không, ghi null, không bịa commit.
`source_tree_sha256` luôn phản ánh bytes đã đóng gói. Output cũ không bị ghi đè;
ZIP chỉ xuất hiện sau khi đóng gói và kiểm checksum thành công. Symlink, `.env*`,
private key và các tệp trạng thái riêng trong cây được đóng gói bị từ chối. Danh
sách này không thể nhận diện mọi loại bí mật trong văn bản: vẫn kiểm tra nguồn trước
khi công khai. Nội dung không đổi và metadata Git không đổi tạo ZIP byte-identical.

Sau chỉnh code, chạy `npm run build` trước khi đóng gói để làm mới offline/worker.
Package script chạy bundle audit nhưng không thay thế toàn bộ QA.

## 5. Nghiệm thu thật

```sh
npm run test:handoff
npm run test:engines
npm run test:production
npm run test:canvas
npm test
npm run test:field
npm run test:skill
```

Kết quả report vẫn ghi `visual: not_reviewed`, `runtime: not_tested`. Dùng quy trình
VFX của skill để review hình ảnh và chạy trong engine đích: import/scale/filter,
origin, front/back, normal/additive trên nền sáng/tối, loop/terminal/transition,
shared combat clock và hiệu năng thiết bị. Compiler/API model/native canvas không
thay thế playback trong Unity, Cocos, Godot hoặc browser/GPU đích.
