#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from j4oauth import main

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    main.app.run('0.0.0.0', port=port, debug=True)
