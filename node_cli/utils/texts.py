#   -*- coding: utf-8 -*-
#
#   This file is part of node-cli
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import yaml
from node_cli.configs import TEXT_FILE


class Texts():
    def __init__(self):
        self._texts = self._load()

    def __getitem__(self, key):
        return self._texts.get(key)

    def _load(self):
        with open(TEXT_FILE, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
