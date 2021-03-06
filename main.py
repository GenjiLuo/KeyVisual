# -*- coding: utf-8 -*-
# @Author: SHLLL
# @Email: shlll7347@gmail.com
# @Date:   2018-04-10 14:51:32
# @Last Modified by:   SHLLL
# @Last Modified time: 2018-05-22 16:43:57
# @License: MIT LICENSE

import logging
import keywordspider as kwspider


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(filename)s[line:%(lineno)d]"
                        " - %(levelname)s: %(message)s")
    kwspider.working(run_server=False, run_spider=False, run_keyword=False,
                     run_assorule=True, max_count=20, use_sql=True)
