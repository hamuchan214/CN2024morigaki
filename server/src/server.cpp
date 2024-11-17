#include<iostream>
#include <boost/asio.hpp>
#include <boost/bind.hpp>
#include <boost/thread.hpp>

using boost::asio::ip::tcp;

const std::string HOST = "127.0.0.1";
const int PORT = 12345;

