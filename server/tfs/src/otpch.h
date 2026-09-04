// Copyright 2022 The Forgotten Server Authors. All rights reserved.
// Use of this source code is governed by the GPL-2.0 License that can be found in the LICENSE file.

#define FS_OTPCH_H_F00C737DA6CA4C8D90F57430C614367F

// Definitions should be global.
#include "definitions.h"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <forward_list>
#include <functional>
#include <iomanip>
#include <iostream>
#include <list>
#include <map>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include <boost/asio.hpp>

#include <pugixml.hpp>

#ifndef FS_ENUM_FORMATTER_PATCH
#define FS_ENUM_FORMATTER_PATCH
#include <fmt/format.h>

#include <type_traits>

// PATCH (Boost 1.92 / fmt >= 10): fmt no longer formats unscoped enums implicitly.
// TFS 1.4.2 passes enums such as AccessList_t / MarketAction_t / MarketOfferState_t
// straight to fmt::format("{:d}", ...). Provide a generic formatter that falls back
// to the enum's underlying integer type so the original call sites keep working.
template <typename E, typename Char>
struct fmt::formatter<E, Char, std::enable_if_t<std::is_enum_v<E>, void>>
    : fmt::formatter<std::underlying_type_t<E>, Char>
{
	template <typename FormatContext>
	auto format(const E& value, FormatContext& ctx) const
	{
		return fmt::formatter<std::underlying_type_t<E>, Char>::format(
		    static_cast<std::underlying_type_t<E>>(value), ctx);
	}
};
#endif
