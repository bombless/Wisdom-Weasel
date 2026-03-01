#pragma once
#include <streambuf>
#include <ios>
#include <istream>
#include <ostream>
#include <cstddef>
#include <cwchar>

// 统一的固定外部缓冲区读写 streambuf，零拷贝。
// 与 boost::interprocess::wbufferstream
// 行为一致：构造后可写可读；写指针和读指针共享同一缓冲区。
class WMemStreamBuf : public std::wstreambuf {
 public:
  WMemStreamBuf(wchar_t* buf, std::size_t len)
      : begin_(buf), size_(len), written_(0) {
    // 同时设置 get 和 put 区域
    setg(buf, buf, buf + len);
    setp(buf, buf + len);
  }
  WMemStreamBuf(const WMemStreamBuf&) = delete;
  WMemStreamBuf& operator=(const WMemStreamBuf&) = delete;

 public:
  // 原始缓冲区指针访问
  wchar_t* buffer() const { return begin_; }
  std::size_t capacity() const { return size_; }
  std::size_t written() const { return written_; }
  std::size_t remaining() const {
    return static_cast<std::size_t>(epptr() - pptr());
  }
  // 重置读写指针到起点，清空已写计数（不清零内容）
  void reset() {
    setg(begin_, begin_, begin_ + size_);
    setp(begin_, begin_ + size_);
    written_ = 0;
  }
  // 将可读区域裁剪到已写入长度，避免读取未写初始化区
  void finalize_read() { setg(begin_, begin_, begin_ + written_); }
  // 安全追加，失败返回false
  bool append(const wchar_t* s, std::size_t count) {
    if (count > remaining())
      return false;
    std::wmemcpy(pptr(), s, count);
    pbump(static_cast<int>(count));
    written_ += count;
    return true;
  }

 protected:
  // 写入单字符（无扩容），写满则失败
  virtual int_type overflow(int_type ch) override {
    if (traits_type::eq_int_type(ch, traits_type::eof())) {
      return traits_type::not_eof(ch);
    }
    if (pptr() == epptr()) {
      return traits_type::eof();
    }
    *pptr() = traits_type::to_char_type(ch);
    pbump(1);
    ++written_;
    return ch;
  }
  // 写入多个字符
  virtual std::streamsize xsputn(const wchar_t* s,
                                 std::streamsize count) override {
    std::streamsize space = epptr() - pptr();
    if (count <= 0)
      return 0;
    if (count > space)
      count = space;
    std::size_t n = static_cast<std::size_t>(count);
    if (n > 0) {
      std::wmemcpy(pptr(), s, n);
      pbump(static_cast<int>(n));
      written_ += n;
    }
    return static_cast<std::streamsize>(n);
  }

 private:
  wchar_t* begin_;
  std::size_t size_;
  std::size_t written_;
};

// 统一读写流，派生自 std::wiostream。
class WMemStream : public std::basic_iostream<wchar_t> {
 public:
  WMemStream(wchar_t* buf, std::size_t len)
      : std::basic_iostream<wchar_t>(nullptr), sbuf_(buf, len) {
    rdbuf(&sbuf_);
  }
  WMemStream(const WMemStream&) = delete;
  WMemStream& operator=(const WMemStream&) = delete;

  // 取得原始缓冲区指针
  wchar_t* data() const { return sbuf_.buffer(); }
  // 当前写入长度（已写入的字符数）
  std::size_t written() const { return sbuf_.written(); }
  std::size_t remaining() const { return sbuf_.remaining(); }
  void reset() { sbuf_.reset(); }
  void finalize_read() { sbuf_.finalize_read(); }
  bool append(const wchar_t* s, std::size_t count) {
    return sbuf_.append(s, count);
  }

 private:
  WMemStreamBuf sbuf_;
};
